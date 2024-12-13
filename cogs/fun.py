import random
from urllib.parse import quote_plus

import discord
import requests
from discord import app_commands
from discord.ext import commands

from views import Confirm


class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, i: discord.Interaction):
        assert self.view is not None
        view = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if view.current_player == view.X and i.user.id == view.p1:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = "It is now O's turn"
        elif view.current_player == view.O and i.user.id == view.p2:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = "It is now X's turn"
        elif (
            view.current_player == view.X
            and i.user.id == view.p2
            or view.current_player == view.O
            and i.user.id == view.p1
        ):
            await i.response.send_message("❌ It's not your turn!", ephemeral=True)
            return
        else:
            await i.response.send_message(
                "❌ You are not part of this game!", ephemeral=True
            )
            return

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = "**X won!**"
            elif winner == view.O:
                content = "**O won!**"
            else:
                content = "**It's a tie!**"

            for child in view.children:
                child.disabled = True

            view.stop()

        await i.response.edit_message(content=content, view=view)


class TicTacToe(discord.ui.View):

    def __init__(self, p1: discord.User, p2: discord.User):
        super().__init__(timeout=60)
        self.X = -1
        self.O = 1
        self.Tie = 2
        self.p1 = p1.id
        self.p2 = p2.id
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        # Our board is made up of 3 by 3 TicTacToeButtons
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    # This method checks for the board winner -- it is used by the TicTacToeButton
    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check vertical
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check diagonals
        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        # If we're here, we need to check if a tie was made
        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None


class RPSButton(discord.ui.Button):
    def __init__(self, label: str, emoji: str):
        super().__init__(label=label, emoji=emoji)

    async def callback(self, i: discord.Interaction):
        view = self.view
        if i.user.id not in (view.p1.id, view.p2.id):
            await i.response.send_message(
                "❌ You are not part of this game.", ephemeral=True
            )
            return

        if view.choices.get(i.user.id):
            await i.response.send_message(
                f"❌ You have already chosen {view.choices[i.user.id]}.", ephemeral=True
            )
            return

        await i.response.defer()
        view.choices[i.user.id] = self.label
        if len(view.choices) == 2:
            if view.choices[view.p1.id] == view.choices[view.p2.id]:
                view.winner = None
            elif (
                view.choices[view.p1.id] == "Rock"
                and view.choices[view.p2.id] == "Scissors"
                or view.choices[view.p1.id] == "Paper"
                and view.choices[view.p2.id] == "Rock"
                or view.choices[view.p1.id] == "Scissors"
                and view.choices[view.p2.id] == "Paper"
            ):
                view.winner = view.p1
            else:
                view.winner = view.p2
            view.stop()


class RockPaperScissors(discord.ui.View):
    def __init__(self, p1: discord.User, p2: discord.User):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.choices = {}
        self.winner = None
        self.add_item(RPSButton(label="Rock", emoji="🪨"))
        self.add_item(RPSButton(label="Paper", emoji="📄"))
        self.add_item(RPSButton(label="Scissors", emoji="✂️"))


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.bot.tree.add_command(
            app_commands.ContextMenu(name="Quote", callback=self.quote_ctx)
        )
        self.bot.tree.add_command(
            app_commands.ContextMenu(name="Mock", callback=self.mock_ctx),
        )
        self.bot.tree.add_command(
            app_commands.ContextMenu(name="Woosh", callback=self.woosh_ctx),
        )

    # tic tac toe
    @app_commands.command(name="tictactoe", description="Play Tic Tac Toe")
    @app_commands.describe(user="The user to play with")
    @app_commands.checks.cooldown(2, 30, key=lambda i: i.user)
    async def tictactoe(self, i: discord.Interaction, user: discord.User):
        if i.user.id == user.id:
            raise ValueError("You can't play with yourself!")
        if user.bot:
            raise ValueError("You can't play with a bot!")

        view = Confirm(user)
        await i.response.send_message(
            content=f"{user.mention}, you have been challenged to **Tic Tac Toe** by {i.user.mention}! Respond within 60 seconds.",
            view=view,
        )
        await view.wait()
        if view.accepted is False:
            return await i.edit_original_response(
                content=f"The challenge was **rejected** by {user.mention}.", view=None
            )
        elif view.accepted is None:
            return await i.edit_original_response(
                content=f"{user.mention} did not respond in time.", view=None
            )

        view = TicTacToe(i.user, user)
        await i.edit_original_response(
            content=f"{i.user.mention} as **X** vs. {user.mention} as **O**", view=view
        )
        timed_out = await view.wait()
        if timed_out:
            await i.edit_original_response(
                content=":information_source: The game timed out.", view=None
            )

    # rock paper scissors
    @app_commands.command(
        name="rockpaperscissors",
        description="Play Rock Paper Scissors with another user",
    )
    @app_commands.describe(user="The user to play with")
    @app_commands.checks.cooldown(2, 30, key=lambda i: i.user)
    async def rps(self, i: discord.Interaction, user: discord.User):
        if i.user.id == user.id:
            raise ValueError("You can't play with yourself!")
        elif user.bot:
            raise ValueError("You can't play with a bot!")

        view = Confirm(user)
        await i.response.send_message(
            f"{user.mention}, you have been challenged to **Rock Paper Scissors** by {i.user.mention}! Respond within 60 seconds.",
            view=view,
        )
        await view.wait()
        if view.accepted is False:
            return await i.edit_original_response(
                content=f"The challenge was **rejected** by {user.mention}.",
                view=None,
            )
        elif view.accepted is None:
            return await i.edit_original_response(
                content=f"{user.mention} did not respond in time.",
                view=None,
            )

        view = RockPaperScissors(i.user, user)
        embed = discord.Embed(
            title="Rock Paper Scissors",
            description=f"### {i.user.mention} vs {user.mention}\nWaiting for players to choose...",
            colour=self.bot.colour,
        )
        await i.edit_original_response(content=None, embed=embed, view=view)
        timed_out = await view.wait()
        if timed_out:
            await i.edit_original_response(
                content=":information_source: The game timed out.",
                view=None,
                embed=None,
            )
            return
        if view.winner is not None:
            winning_choice = (
                view.choices[i.user.id]
                if view.winner == view.p1
                else view.choices[user.id]
            )
            losing_choice = (
                view.choices[user.id]
                if view.winner == view.p1
                else view.choices[i.user.id]
            )
            embed.description = f"### {view.winner.mention} is the **winner!**"
            embed.add_field(name="Winning pick:", value=winning_choice)
            embed.add_field(name="Losing pick:", value=losing_choice)
            await i.edit_original_response(embed=embed, view=None)
        else:
            embed.description = "### It's a tie!"
            embed.add_field(name="Both players chose:", value=view.choices[i.user.id])
            await i.edit_original_response(embed=embed, view=None)

    # quote (ctxmenu)
    @app_commands.checks.cooldown(2, 20, key=lambda i: i.channel)
    async def quote_ctx(self, i: discord.Interaction, message: discord.Message):
        if not 0 < len(message.content) <= 100:
            raise ValueError("The text must have 1-100 characters.")
        await i.response.defer()
        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"a beautiful quote from {message.author.display_name}",
        )
        embed.set_image(
            url=(
                f"https://api.popcat.xyz/quote?image={quote_plus(message.author.display_avatar.url)}"
                f"&text={quote_plus(message.content)}"
                f"&name={quote_plus(message.author.display_name)}"
            )
        )

        await i.followup.send(embed=embed)

    # quote
    @app_commands.command(name="quote", description="Create a quote image")
    @app_commands.describe(
        quote="The quote", user="The author of the quote (default: yourself)"
    )
    @app_commands.checks.cooldown(2, 20, key=lambda i: i.channel)
    async def quote(
        self, i: discord.Interaction, quote: str, user: discord.Member = None
    ):
        if user is None:
            user = i.user
        if len(quote) > 100:
            raise ValueError("The text must have no more than 100 characters.")
        await i.response.defer()
        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"a beautiful quote from {user.display_name}",
        )
        embed.set_image(
            url=(
                "https://api.popcat.xyz/quote?image="
                f"{quote_plus(user.display_avatar.url)}"
                f"&text={quote_plus(quote)}"
                f"&name={quote_plus(user.display_name)}"
            )
        )

        await i.followup.send(embed=embed)

    # pickupline
    @app_commands.command(name="pickupline", description="Get a pickup line")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.channel)
    async def pickupline(self, i: discord.Interaction):
        await i.response.defer()
        r = requests.get("https://api.popcat.xyz/pickuplines")
        json = r.json()
        if json.get("pickupline"):
            pickupline = json["pickupline"]
            await i.followup.send(pickupline)
        else:
            raise ValueError("Couldn't retrieve data. Try again later.")

    # 8ball
    @app_commands.command(name="8ball", description="Ask the Magic 8Ball a question")
    @app_commands.describe(question="The question to ask")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.channel)
    async def _8ball(self, i: discord.Interaction, question: str):
        responses = [
            # Affirmative
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            # Non-committal
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not to tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            # Negative
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        fortune = random.choice(responses)
        embed = discord.Embed(
            colour=self.bot.colour,
        )
        if len(question) > 256:
            embed.title = f'"{question[:251]}..."'
        else:
            embed.title = f'"{question}"'
        embed.add_field(name="🎱 The Magic 8Ball says:", value=f"||{fortune}||")
        await i.response.send_message(embed=embed)

    # coinflip
    @app_commands.command(name="coinflip", description="Flip a coin")
    @app_commands.checks.cooldown(3, 15, key=lambda i: i.channel)
    async def coinflip(self, i: discord.Interaction):
        await i.response.send_message(
            f"🪙 Flipped a coin for you, it's **{random.choice(('heads', 'tails'))}**!"
        )

    # dice
    @app_commands.command(name="dice", description="Roll dice")
    @app_commands.checks.cooldown(3, 15, key=lambda i: i.channel)
    @app_commands.describe(
        number="The number of dice to roll",
    )
    async def dice(self, i: discord.Interaction, number: int = 1):
        if not 1 <= number <= 6:
            raise ValueError("The number of dice must be between 1 and 6.")
        rolls = random.sample(range(1, 7), number)
        await i.response.send_message(
            f"🎲 Rolled {number} dice: {', '.join([str(r) for r in rolls])}"
        )

    # mock (ctxmenu)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.channel)
    async def mock_ctx(self, i: discord.Interaction, message: discord.Message):
        if not message.content:
            raise ValueError("The message has no text.")
        await self.mock.callback(self, i, message.content)

    # mock
    @app_commands.command(name="mock", description="Mock text")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.channel)
    @app_commands.describe(text="The text to mock")
    async def mock(self, i: discord.Interaction, text: str):
        if len(text) > 2000:
            raise ValueError("The text must be no more than 2000 characters.")
        mock_text = "".join(
            [char.upper() if i % 2 else char.lower() for i, char in enumerate(text)]
        )

        await i.response.send_message(
            mock_text,
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    # dadjoke
    @app_commands.command(name="dadjoke", description="Get a dad joke")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.channel)
    async def dadjoke(self, i: discord.Interaction):
        r = requests.get(
            "https://icanhazdadjoke.com/", headers={"Accept": "application/json"}
        )
        if not r.ok:
            raise ValueError("Couldn't retrieve data. Try again later.")
        await i.response.defer()
        joke = r.json()["joke"]
        await i.followup.send(joke)

    # dog
    @app_commands.command(name="dog", description="Get a random dog image and fact")
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.channel)
    async def dog(self, i: discord.Interaction):
        await i.response.defer()
        r = requests.get("https://some-random-api.com/animal/dog")
        if not r.ok:
            raise ValueError("Couldn't retrieve data. Try again later.")

        json = r.json()
        embed = discord.Embed(colour=self.bot.colour)
        embed.set_image(url=json["image"])
        embed.set_footer(text="Dog fact: " + json["fact"])
        await i.followup.send(embed=embed)

    # cat
    @app_commands.command(name="cat", description="Get a random cat image and fact")
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.channel)
    async def cat(self, i: discord.Interaction):
        await i.response.defer()
        r = requests.get("https://some-random-api.com/animal/cat")
        if not r.ok:
            raise ValueError("Couldn't retrieve data. Try again later.")

        json = r.json()
        embed = discord.Embed(colour=self.bot.colour)
        embed.set_image(url=json["image"])
        embed.set_footer(text="Cat fact: " + json["fact"])
        await i.followup.send(embed=embed)

    # panda
    @app_commands.command(name="panda", description="Get a random panda image and fact")
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.channel)
    async def panda(self, i: discord.Interaction):
        await i.response.defer()
        r = requests.get("https://some-random-api.com/animal/panda")
        if not r.ok:
            raise ValueError("Couldn't retrieve data. Try again later.")

        json = r.json()
        embed = discord.Embed(colour=self.bot.colour)
        embed.set_image(url=json["image"])
        embed.set_footer(text="Panda fact: " + json["fact"])
        await i.followup.send(embed=embed)

    # megamind
    @app_commands.command(name="megamind", description="Generate a megamind meme")
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.channel)
    async def megamind(self, i: discord.Interaction, text: str):
        if len(text) > 200:
            raise ValueError("The text must be no more than 200 characters.")

        r = requests.get(
            f"https://some-random-api.com/canvas/misc/nobitches?no={quote_plus(text)}"
        )
        if not r.ok:
            raise ValueError("Couldn't retrieve data. Try again later.")

        embed = discord.Embed(colour=self.bot.colour)
        embed.set_image(
            url=f"https://some-random-api.com/canvas/misc/nobitches?no={quote_plus(text)}"
        )
        await i.response.send_message(embed=embed)

    # woosh
    @app_commands.command(
        name="woosh", description="Generate a woosh (joke-over-head) image"
    )
    @app_commands.describe(user="The user who didn't get the joke")
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.channel)
    async def woosh(self, i: discord.Interaction, user: discord.Member | discord.User):
        # remove url parameters at the end of avatar url
        avatar = user.display_avatar.replace(format="png").url
        embed = discord.Embed(
            colour=self.bot.colour,
            description=f"Woosh... that's the sound of a joke going over {user.display_name}'s head",
        )
        embed.set_image(url=f"https://api.popcat.xyz/jokeoverhead?image={avatar}")
        await i.response.send_message(embed=embed)

    # woosh (ctxmenu)
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.channel)
    async def woosh_ctx(
        self, i: discord.Interaction, user: discord.Member | discord.User
    ):
        await self.woosh.callback(self, i, user)

    # xkcd
    @app_commands.command(name="xkcd", description="Get xkcd comics")
    @app_commands.describe(mode="Random or latest comic (default: random)")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="random", value="random"),
            app_commands.Choice(name="latest", value="latest"),
        ]
    )
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.channel)
    async def xkcd(self, i: discord.Interaction, mode: str = "random"):
        r = requests.get("https://xkcd.com/info.0.json")
        if not r.ok:
            raise ValueError("Couldn't retrieve data. Try again later.")
        json = r.json()

        if mode == "random":
            latest_num = r.json()["num"]
            comic_num = random.randint(1, latest_num)
            r = requests.get(f"https://xkcd.com/{comic_num}/info.0.json")
            if not r.ok:
                raise ValueError("Couldn't retrieve data. Try again later.")
            json = r.json()

        embed = discord.Embed(
            title=f"xkcd #{json['num']}: {json['safe_title']}",
            description=f"[Comic explanation](https://explainxkcd.com/{json['num']})",
            url=f"https://xkcd.com/{json['num']}",
            colour=self.bot.colour,
        )
        embed.set_image(url=json["img"])
        await i.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
