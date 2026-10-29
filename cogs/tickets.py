import asyncio
import logging
import re
import time

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.i18n import t
from utils.transcript import build_transcript

COLOR = discord.Color.from_str("#F5B83D")
log = logging.getLogger("beacon.tickets")

SUPPORT = "support"
PARTNERSHIP = "partnership"


# Helpers

def is_staff(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(
        r.id == config.STAFF_ROLE_ID for r in member.roles
    )


def clean_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "", name.lower())[:80] or "user"


def parse_topic(topic: str | None):
    """Ticket channels store 'ticket:<user_id>:<kind>' in their topic."""
    if topic and topic.startswith("ticket:"):
        _, user_id, kind = topic.split(":", 2)
        return int(user_id), kind
    return None


async def report_error(interaction: discord.Interaction, error: Exception):
    """Log the full error and show the user only a generic message."""
    log.error(
        "Interaction failed (user=%s, channel=%s)",
        interaction.user.id, interaction.channel_id, exc_info=error,
    )
    try:
        if interaction.response.is_done():
            await interaction.followup.send(t("error.generic"), ephemeral=True)
        else:
            await interaction.response.send_message(t("error.generic"), ephemeral=True)
    except discord.HTTPException:
        pass


class SafeModal(discord.ui.Modal):
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await report_error(interaction, error)


class SafeView(discord.ui.View):
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        await report_error(interaction, error)


# Modals

class SupportModal(SafeModal, title=t("modal.support.title")):
    problem = discord.ui.TextInput(
        label=t("modal.support.problem"),
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    def __init__(self, cog: "Tickets"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.create_ticket(
            interaction, SUPPORT, [(t("modal.support.problem"), self.problem.value)]
        )


class PartnershipModal(SafeModal, title=t("modal.partnership.title")):
    server_name = discord.ui.TextInput(label=t("modal.partnership.name"), max_length=100)
    invite = discord.ui.TextInput(
        label=t("modal.partnership.invite"), placeholder="https://discord.gg/...", max_length=100
    )
    members = discord.ui.TextInput(label=t("modal.partnership.members"), max_length=10)
    reason = discord.ui.TextInput(
        label=t("modal.partnership.reason"),
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    def __init__(self, cog: "Tickets"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.create_ticket(
            interaction,
            PARTNERSHIP,
            [
                (t("modal.partnership.name"), self.server_name.value),
                (t("modal.partnership.invite"), self.invite.value),
                (t("modal.partnership.members"), self.members.value),
                (t("modal.partnership.reason"), self.reason.value),
            ],
        )


# Panel

class PanelView(SafeView):
    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.select(
        custom_id="beacon:panel",
        placeholder=t("panel.placeholder"),
        options=[
            discord.SelectOption(
                label=t("panel.option.support.label"),
                description=t("panel.option.support.description"),
                value=SUPPORT,
                emoji="🛠️",
            ),
            discord.SelectOption(
                label=t("panel.option.partnership.label"),
                description=t("panel.option.partnership.description"),
                value=PARTNERSHIP,
                emoji="🤝",
            ),
        ],
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        existing = self.cog.find_open_ticket(interaction.guild, interaction.user.id)
        until = self.cog.cooldown_until(interaction.user)

        if existing:
            await interaction.response.send_message(
                t("ticket.already_open", channel=existing.mention), ephemeral=True
            )
        elif until:
            await interaction.response.send_message(
                t("ticket.cooldown", time=f"<t:{until}:R>"), ephemeral=True
            )
        elif select.values[0] == SUPPORT:
            await interaction.response.send_modal(SupportModal(self.cog))
        else:
            await interaction.response.send_modal(PartnershipModal(self.cog))

        # Reset the menu so the same option can be picked again
        await interaction.message.edit(view=PanelView(self.cog))


# Tickets Buttons

class TicketView(SafeView):
    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label=t("ticket.claim_button"), emoji="🙋",
        style=discord.ButtonStyle.success, custom_id="beacon:claim",
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction.user):
            await interaction.response.send_message(t("error.staff_only"), ephemeral=True)
            return

        view = TicketView(self.cog)
        view.claim.disabled = True
        view.claim.label = t("ticket.claimed_label", name=interaction.user.display_name)[:80]
        await interaction.response.edit_message(view=view)
        await interaction.channel.send(embed=discord.Embed(
            description=t("ticket.claimed", user=interaction.user.mention), color=COLOR
        ))

    @discord.ui.button(
        label=t("ticket.close_button"), emoji="🔒",
        style=discord.ButtonStyle.danger, custom_id="beacon:close",
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = parse_topic(interaction.channel.topic)
        if not data:
            return
        if not (is_staff(interaction.user) or interaction.user.id == data[0]):
            await interaction.response.send_message(t("error.cannot_close"), ephemeral=True)
            return
        await interaction.response.send_message(
            t("ticket.close_question"), view=ConfirmCloseView(self.cog), ephemeral=True
        )


class ConfirmCloseView(SafeView):
    def __init__(self, cog: "Tickets"):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.button(label=t("ticket.close_confirm"), style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=t("ticket.closing"), view=None)
        await self.cog.close_ticket(interaction.channel, interaction.user)

    @discord.ui.button(label=t("ticket.close_cancel"), style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=t("ticket.close_cancelled"), view=None)


# Cog

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.closing: set[int] = set()
        # user_id -> unix time when the user can open a new ticket (kept in memory only)
        self.cooldowns: dict[int, float] = {}

    async def cog_load(self):
        # Keep buttons and menus working after a bot restart
        self.bot.add_view(PanelView(self))
        self.bot.add_view(TicketView(self))

    def find_open_ticket(self, guild: discord.Guild, user_id: int):
        for category_id in config.TICKET_CATEGORIES.values():
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                continue
            for channel in category.text_channels:
                data = parse_topic(channel.topic)
                if data and data[0] == user_id:
                    return channel
        return None

    def cooldown_until(self, member: discord.Member) -> int | None:
        """Unix timestamp when `member` can open a new ticket, or None if they can right now."""
        if is_staff(member):
            return None
        until = self.cooldowns.get(member.id)
        if until is None or until <= time.time():
            self.cooldowns.pop(member.id, None)
            return None
        return int(until)

    async def create_ticket(self, interaction: discord.Interaction, kind: str, answers: list[tuple[str, str]]):
        guild, user = interaction.guild, interaction.user

        existing = self.find_open_ticket(guild, user.id)
        if existing:
            await interaction.response.send_message(
                t("ticket.already_open", channel=existing.mention), ephemeral=True
            )
            return

        until = self.cooldown_until(user)
        if until:
            await interaction.response.send_message(
                t("ticket.cooldown", time=f"<t:{until}:R>"), ephemeral=True
            )
            return

        category = guild.get_channel(config.TICKET_CATEGORIES[kind])
        staff_role = guild.get_role(config.STAFF_ROLE_ID)
        if not isinstance(category, discord.CategoryChannel) or staff_role is None:
            await interaction.response.send_message(t("ticket.invalid_config"), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        access = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True,
        )
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: access,
            staff_role: access,
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True, manage_channels=True,
            ),
        }

        channel = await guild.create_text_channel(
            name=f"{t(f'ticket.prefix.{kind}')}-{clean_name(user.name)}",
            category=category,
            overwrites=overwrites,
            topic=f"ticket:{user.id}:{kind}",
            reason=f"{kind} ticket opened by {user}",
        )

        embed = discord.Embed(
            title=t(f"ticket.title.{kind}"),
            description=t("ticket.welcome", user=user.mention),
            color=COLOR,
        )
        for name, value in answers:
            embed.add_field(name=name, value=value[:1024] or "—", inline=False)
        embed.set_footer(text=t("ticket.footer"))

        await channel.send(
            content=f"{user.mention} {staff_role.mention}",
            embed=embed,
            view=TicketView(self),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )
        await interaction.followup.send(t("ticket.created", channel=channel.mention), ephemeral=True)

    async def close_ticket(self, channel: discord.TextChannel, closer: discord.Member):
        data = parse_topic(channel.topic)
        if not data or channel.id in self.closing:
            return
        self.closing.add(channel.id)

        try:
            issuer_id = data[0]
            try:
                issuer = channel.guild.get_member(issuer_id) or await self.bot.fetch_user(issuer_id)
                issuer_name = str(issuer)
            except discord.NotFound:
                issuer_name = t("ticket.unknown_user", id=issuer_id)

            await channel.send(embed=discord.Embed(
                description=t("ticket.closed_notice", user=closer.mention),
                color=discord.Color.red(),
            ))

            opened_at = channel.created_at
            closed_at = discord.utils.utcnow()
            file = await build_transcript(channel, issuer_name, str(closer), opened_at, closed_at)

            embed = discord.Embed(title=t("transcript.title"), color=COLOR)
            embed.add_field(name=t("transcript.name"), value=f"`{channel.name}`", inline=False)
            embed.add_field(name=t("transcript.issuer"), value=f"<@{issuer_id}> ({issuer_name})", inline=False)
            embed.add_field(name=t("transcript.closed_by"), value=f"{closer.mention} ({closer})", inline=False)
            embed.add_field(name=t("transcript.opened_at"), value=discord.utils.format_dt(opened_at, "F"))
            embed.add_field(name=t("transcript.closed_at"), value=discord.utils.format_dt(closed_at, "F"))

            log_channel = channel.guild.get_channel(config.TRANSCRIPT_CHANNEL_ID)
            await log_channel.send(file=file, embed=embed)

            # The cooldown starts when the previous ticket is closed
            self.cooldowns[issuer_id] = time.time() + config.TICKET_COOLDOWN

            await asyncio.sleep(5)
            await channel.delete(reason=f"Ticket closed by {closer}")
        except Exception:
            # The channel is NOT deleted, so nothing is lost
            log.exception("Failed to close ticket #%s (%s)", channel.name, channel.id)
            self.closing.discard(channel.id)
            try:
                await channel.send(t("ticket.close_error"))
            except discord.HTTPException:
                pass

    async def cog_app_command_error(self, interaction: discord.Interaction, error: Exception):
        await report_error(interaction, error)

    # Slash commands

    @app_commands.command(name="ticket-panel", description=t("cmd.ticket_panel.description"))
    @app_commands.guild_only()
    async def ticket_panel(self, interaction: discord.Interaction):
        if not is_staff(interaction.user):
            await interaction.response.send_message(t("error.staff_only"), ephemeral=True)
            return

        embed = discord.Embed(
            title=t("panel.title"), description=t("panel.description"), color=COLOR
        )
        await interaction.channel.send(embed=embed, view=PanelView(self))
        await interaction.response.send_message(t("panel.created"), ephemeral=True)

    @app_commands.command(name="add", description=t("cmd.add.description"))
    @app_commands.describe(user=t("cmd.add.user"))
    @app_commands.guild_only()
    async def add(self, interaction: discord.Interaction, user: discord.Member):
        if not parse_topic(interaction.channel.topic):
            await interaction.response.send_message(t("error.ticket_only"), ephemeral=True)
            return
        if not is_staff(interaction.user):
            await interaction.response.send_message(t("error.staff_only"), ephemeral=True)
            return
        await interaction.channel.set_permissions(
            user, view_channel=True, send_messages=True, read_message_history=True, attach_files=True
        )
        await interaction.response.send_message(t("ticket.user_added", user=user.mention))

    @app_commands.command(name="remove", description=t("cmd.remove.description"))
    @app_commands.describe(user=t("cmd.remove.user"))
    @app_commands.guild_only()
    async def remove(self, interaction: discord.Interaction, user: discord.Member):
        data = parse_topic(interaction.channel.topic)
        if not data:
            await interaction.response.send_message(t("error.ticket_only"), ephemeral=True)
            return
        if not is_staff(interaction.user):
            await interaction.response.send_message(t("error.staff_only"), ephemeral=True)
            return
        if user.id == data[0]:
            await interaction.response.send_message(t("error.cannot_remove_issuer"), ephemeral=True)
            return
        if user == interaction.guild.me:
            await interaction.response.send_message(t("error.cannot_remove_bot"), ephemeral=True)
            return
        await interaction.channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(t("ticket.user_removed", user=user.mention))


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))