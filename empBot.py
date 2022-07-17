import discord
import tweepy
import aiohttp
import asyncio
import os
import io
import bs4 as bs
import urllib.request
import random
from urllib.request import urlopen, URLError
from discord.ext import commands, tasks

# TF2 Emporium Bot
# Coded by rabscootle#1998

# NOTE: API Keys + Channel IDs have been purged for privacy reasons.

# TWITTER KEYS (...would go here)
consumer_key = None
consumer_secret = None
access_token = None
access_token_secret = None

# DISCORD KEY (...would go here)
discord_key = None

def validate_web_url(url="http://google"):
    try:
        urlopen(url)
        return True
    except URLError:
        return False

client = commands.Bot(command_prefix = ['.', '!'])
client.remove_command('help')


# VALID YES/NO RESPONSES
valid_yes = ['y', 'yes', 'yeah', 'sure', 'uh-huh', 'yuh', 'yah', 'yass', 'okay', 'ok', 'mhm', 'si', 'da']

# Banner stuff (for Discord server)
banner_prefix = 'http://neodem.net/tf2empbanners/'
banner_links = ['default.png']
banner_names = ['Default']

def OAuth():
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        return auth
    except Exception as e:
        return None

oauth = OAuth()
api = tweepy.API(oauth)

async def fetch_img(session, url):
    #with aiohttp.Timeout(10):
    async with session.get(url) as response:
        assert response.status == 200
        return await response.read()

async def tweet(image, message, reply):
    item_tweet = api.update_with_media(image, status = message)
    os.remove(image)
    epic = api.update_status(reply, in_reply_to_status_id = item_tweet.id)
    return epic

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Use .empinfo!'))
    channel = client.get_channel(None) #this should be bot-misc
    #await channel.send(random.choice(responses)) # SENDS LIVE MESSAGE
    print('Bot is ready!')

    argnum = random.randint(1, len(banner_links))
    img_url = banner_prefix + banner_links[argnum - 1]
    #print(img_url) #DEBUG

    # image download code
    loop = asyncio.get_event_loop()
    imgSesh = aiohttp.ClientSession(loop=loop).get(img_url)
    async with imgSesh as resp:
        assert resp.status == 200
        await channel.guild.edit(banner = await resp.read()) # resp.read() =  bytes object for discord banner
    imgSesh.close()

    #await channel.send('Showcased item changed to ' + banner_names[argnum - 1])

# @client.event
# async def on_member_join(member):
#     print(f'{member} has joined a server.')

# @client.event
# async def on_member_remove(member):
#     print(f'{member} has left a server.')

@client.event
async def on_reaction_add(reaction, user):
    #print(reaction.message.content)
    channel = reaction.message.channel
    #print(str(reaction.emoji))
    if(reaction.message.channel.name == "approval" and (str(reaction.emoji) == '<:engythumb:468840724830355476>') and reaction.count == 2 and (reaction.message.content.startswith('Pending item approval! @here'))):
        embedMsg = reaction.message.embeds[0]
        subType = embedMsg.description
        itemName = embedMsg.title
        itemURL = embedMsg.url

        kritzKast_approved = False

        if('[APPROVED FOR KRITZKAST]' in reaction.message.content):
            kritzKast_approved = True

        # TWITTER
        imgURL = embedMsg.image.url
            # Downloading images.
        loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession(loop=loop) as session:
            image = await fetch_img(session,imgURL)
        with open("img.png", "wb") as f:
            f.write(image)
        tweetMessage = "New " + subType + ", " + itemName + "! Vote now on Steam Workshop: " + itemURL
        
        # # ADDING KRITZKAST MENTION TO TWEET
        # if(kritzKast_approved == True):
        #     tweetMessage = tweetMessage + " @KritzKast"

        tweetMessage = tweetMessage + " #TF2"
        contribs = embedMsg.fields[0].value.split(', ')

        isCollection = False
        if("Collection" in subType):
            isCollection = True

        # EXTRACTING WORKSHOP PROFILE LINKS
        page = urllib.request.urlopen(embedMsg.url)
        soup = bs.BeautifulSoup(page, 'lxml')
        contribLinks = []

        #print("WE HAVE OPENED THE PAGE")
        if (isCollection is False):
            urlHUB = soup.find('div', class_= 'creatorsBlock')
            #print(urlHUB) #DEBUG
            for contribLink in urlHUB.find_all('a', class_='friendBlockLinkOverlay', attrs = 'href'):
                # prints the p tag content
                contribLinks.append(contribLink.get('href'))
        else: # This is if we are currently in a collection, the first featured item's page will be loaded to grab all contributor names.
            urlHUB = soup.find('div', class_= 'clearfix collection')
            urlHUB = urlHUB.find_all('div', class_= 'collectionItemDetails', attrs = 'href')[0]
            itemLink = urlHUB.find('a', href = True)['href']

            page = urllib.request.urlopen(itemLink)
            soup = bs.BeautifulSoup(page, 'lxml')

            # Assuming we are now in the item page, do the same thing as if we were handling a single item.
            urlHUB = soup.find('div', class_= 'creatorsBlock')
            for contribLink in urlHUB.find_all('a', class_='friendBlockLinkOverlay', attrs = 'href'):
                contribLinks.append(contribLink.get('href'))


        # Contributor reply content.
        if(isCollection is True):
            contribMsg = "This collection was created by:\n"
        else:
            contribMsg = "This item was created by:\n"

        contribIndex = len(contribs) - 1
        while (contribIndex >= 0):
            contribMsg = contribMsg + contribs[contribIndex] + " (" + contribLinks[contribIndex] + ")"
            if(contribIndex != 0):
                contribMsg = contribMsg + "\n"

            contribIndex -= 1 # I forgot this like an absolute chimp.


        #print("TWEETING!!")
        tweet_status = await tweet('img.png', tweetMessage, contribMsg)
        
        approvedStr = ""
        approvedStr = approvedStr + itemName + " has been approved for Twitter release by: | "
        async for user in reaction.users():
            approvedStr = approvedStr + user.name + " | "

        if(kritzKast_approved == True):
            approvedStr = approvedStr + "[KRITZKAST APPROVED]"


        await channel.send(approvedStr, embed = embedMsg)

        if(kritzKast_approved == True):
            kk_channel = client.get_channel(None)
            await kk_channel.send(embed = embedMsg) # SENDS EMBED TO TF2 EMPORIUM CHANNEL ON KRITZKAST SERVER

        await reaction.message.delete() #deletes mesage from page (removed)


@client.command()
async def empinfo(ctx):
    #print(f'{ctx.author} has attempted submitting an item')
    await ctx.message.delete()
    msg = await ctx.author.send('To submit an item to #releases and the TF2 Emporium Twitter (@TF2Emporium), type .release or .submit in #discussion.\nPlease note your item may take some time to appear on the Twitter as each submission is manually approved by staff members.')

# SAY COMMAND
@commands.guild_only()
@client.command()
async def say(ctx):
    role = discord.utils.get(ctx.guild.roles, name = 'Bot')
    if role in ctx.author.roles:
        await ctx.message.delete()
        #channel = client.get_channel(None)
        msg = ctx.message.content[5:]
        #print(msg)
        await ctx.channel.send(msg)#, tts = True)
        #await ctx.channel.send('') # SENDS EMBED TO RELEASES
    else:
        await ctx.message.delete()
        await ctx.author.send(random.choice(denied_responses))

# SPEAK COMMAND
@commands.guild_only()
@client.command()
async def speak(ctx):
    #print(f'{ctx.author} has attempted submitting an item')
    role = discord.utils.get(ctx.guild.roles, name = 'Bot')
    if role in ctx.author.roles:
        await ctx.message.delete()
        #channel = client.get_channel(None)
        msg = '<:dell:651987754615308293>**<( **'
        msg = msg + ctx.message.content[7:] + '** )**'
        #print(msg)
        if(len(ctx.message.content[7:]) > 0):
            await ctx.channel.send(msg)
        #await ctx.channel.send('') # SENDS EMBED TO RELEASES
    else:
        await ctx.message.delete()
        await ctx.author.send(random.choice(denied_responses))

# STATS COMMAND
@commands.guild_only()
@client.command()
async def recon(ctx):
    await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name = 'Bot')
    if role in ctx.author.roles:
        for channel in ctx.message.guild.voice_channels:
            print(channel.name)
            if len(channel.members) > 0:
                for member in channel.members:
                    print(member.name)
    else:
        await ctx.author.send(random.choice(denied_responses))

@commands.guild_only()
@client.command()
async def postupdate(ctx, arg):
    await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name = 'Bot')
    if role in ctx.author.roles:
        if(arg.startswith('https://www.teamfortress.com/post.php?id=')):
            link = arg
            updateMsg = "An update for Team Fortress 2 has been released.\nYou can read the patch notes here: " + link + " #TF2"
            aha = api.update_status(updateMsg)
        else:
            ctx.channel.send('Invalid Link Input')
    else:
        await ctx.author.send(random.choice(denied_responses))

# Banner Debug Command
@commands.guild_only()
@client.command(aliases = ['currbanner', 'currBanner'])
async def _currBanner(ctx):
    #await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name = 'Bot')
    if role in ctx.author.roles:
        await ctx.channel.send('Current banner url is ' + str(ctx.message.guild.banner_url))
    else:
        await ctx.author.send(random.choice(denied_responses))

# Banner Index Command
@commands.guild_only()
@client.command(aliases = ['bannerindex', 'bannerIndex'])
async def _bannerIndex(ctx):
    #await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name = 'Bot')
    if role in ctx.author.roles:
        bannIndex = 'Current banner rotation is:\n'
        index = 0
        while index < len(banner_names):
            bannIndex = bannIndex + str(index + 1) + '. ' + banner_names[index]
            index = index + 1
            if(index < len(banner_names)):
                bannIndex = bannIndex + '\n'
        await ctx.channel.send(bannIndex)
    else:
        await ctx.author.send(random.choice(denied_responses))

# Banner Changing Command
@commands.guild_only()
@client.command(aliases = ['changebanner', 'changeBanner', 'setbanner', 'setBanner'])
async def _changeBanner(ctx, arg):
    #await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name = 'Bot')
    if role in ctx.author.roles:
        argnum = int(arg)
        if(argnum <= len(banner_links) and argnum > 0):
            img_url = banner_prefix + banner_links[argnum - 1]
            print(img_url)

            # image download code
            loop = asyncio.get_event_loop()
            imgSesh = aiohttp.ClientSession(loop=loop).get(img_url)
            async with imgSesh as resp:
                assert resp.status == 200
                await ctx.guild.edit(banner = await resp.read()) # resp.read() =  bytes object for discord banner
            imgSesh.close()

            await ctx.channel.send('Showcased item changed to ' + banner_names[argnum - 1])
        else:
            await ctx.channel.send('Inputted banner index ('  + argnum + ') out of range.')
    else:
        await ctx.author.send(random.choice(denied_responses))



@client.command(aliases = ['release', 'submit'])
async def _release(ctx): #something like (ctx *, name) would just mean it ignores all the text
    #await delete(command, delay=None)
    if(ctx.channel.name == "discussion"):
        #print(f'{ctx.author} has attempted submitting an item')
        curr_step = 0
        num_contribs = 0
        contribs = []
        canceled = False
        await ctx.message.delete()
        #imgLink = ""
        msg = await ctx.author.send('Hello! It seems you are trying to submit an item. To restart the process at any time, type *restart*. To cancel the process, just type *cancel*.\nIf I stop responding at any point just start over and type *.submit* or *.release* in #discussions.\nIf multiple instances of me begin to exist, just type *cancel* and restart the process.\n\n')
        #tweetMessage = ""
        isTF2 = False
        isCollection = False

        # STEPS
        while(curr_step < 4):

            def check(message):
                return message.author == ctx.author and message.channel == msg.channel

            # LINK INPUT
            if(curr_step == 0):
                #print("Currently in link submission step.")
                kk_approved = False # Bool for KritzKast partnership!
                isPersonal = False
                valid_link = False
                isTF2 = False
                isCollection = False
                tf2_icon = 'https://wiki.teamfortress.com/w/images/b/be/TF2_crosshair_orange.png'
                #csgo_icon = '' #TODO
                #dota_icon = '' #TODO
                #sfm_icon = '' #TODO
                #rust_icon = '' #TODO
                tf2_color = 0xB98A2E
                holiday_color = tf2_color
                holiday_thumb = tf2_icon
                msg = await ctx.author.send('**First let me have your item\'s Steam Workshop link.**')
                #https://steamcommunity.com/sharedfiles/filedetails/?id=1924815269
                while(valid_link is False):
                    link = await client.wait_for('message', check=check)
                    if (link.content.startswith('https://steamcommunity.com/sharedfiles/filedetails/?id=') or link.content.startswith('https://www.steamcommunity.com/sharedfiles/filedetails/?id=')
                        or link.content.startswith('www.steamcommunity.com/sharedfiles/filedetails/?id=') or link.content.startswith('steamcommunity.com/sharedfiles/filedetails/?id=')
                        or link.content.startswith('https://steamcommunity.com/workshop/') or link.content.startswith('steamcommunity.com/workshop/') or link.content.startswith('www.steamcommunity.com/workshop/')
                        or link.content.startswith('https://www.steamcommunity.com/workshop/') or link.content.startswith('restart') 
                        or link.content.startswith('Restart') or link.content.startswith('cancel') or link.content.startswith('Cancel')):
                    #await name.channel.send(f'{link.content} received!')
                        link = link.content
                        valid_link = True
                    if(valid_link is False):
                        msg = await ctx.author.send('**Oops! It seems your link isn\'t one from Steam Community. Please make sure your link is valid.**')

                if (link.startswith('restart') or link.startswith('Restart')):
                    curr_step = 0
                elif(link.startswith('cancel') or link.startswith('Cancel')):
                    curr_step = 6
                    canceled = True
                else:
                    item_id = link.split('=')[1]
                    item_id = item_id.split('&')[0]
                    curr_step = curr_step + 1

                    holiday = ""
                    merc = ""
                    item_type = ""
                    game_type = ""

                    # Web scrubbing junk
                    page = urllib.request.urlopen(link)
                    soup = bs.BeautifulSoup(page, 'lxml')

                    # Game title extraction.
                    game = soup.find('div', class_= 'apphub_AppName ellipsis')
                    game = game.text
                    if(game == 'Team Fortress 2'):
                        isTF2 = True
                        #print('TF2 Submission Detected!')
                    else:
                        holiday = game
                        holiday_color = 0x484e6b

                    #Name Extraction
                    title = soup.find('div', class_= 'workshopItemTitle')
                    #print(title) #DEBUG
                    name = title.text
                    #print(name) #DEBUG
                    
                    #Workshop Tag Extraction
                    tags = soup.find('div', class_= 'col_right')
                    if(tags is None):
                        tags = soup.find('div', class_= 'sidebar')
                        item_type = 'Collection'
                        isCollection = True
                        
                    tagArr = []
                    for ptag in tags.find_all('div', class_='workshopTags'):
                        # prints the p tag content
                        tagArr.append(ptag.text)

                    for tagz in tagArr:
                        if (tagz.startswith("Class:")):
                            #print(tagz) #DEBUG
                            people = tagz.split(":")[1][1:]
                            #print(people) #DEBUG
                            mercs = people.split(',')
                            if(len(mercs) == 1):
                                merc = mercs[0]
                            else:
                                if(len(mercs) < 9):
                                    merc = "Multi-Class"
                                else:
                                    merc = "All-Class"



                        if (tagz.startswith("Item Slot:")):
                            # ITEM TYPE EXTRACTION
                            #print(tagz) #DEBUG
                            slot = tagz.split(":")[1][1:]
                            #print(slot) #DEBUG

                            if(len(slot.split(",")) > 1):
                                slot = 'Cosmetic'
                            if(len(item_type) == 0):
                                item_type = slot
                            #print(item_type) #DEBUG

                        # OTHER TAGS
                        if (tagz.startswith("Other:")):
                            #print(tagz) #DEBUG

                            others = tagz.split(":")[1]
                            others = others.split(',')
                            #print(others) # DEBUG
                            holidayCount = 0
                            for stuff in others:
                                #print(stuff)
                                if(stuff[1:] == 'Halloween' or stuff[1:] == 'Smissmas'):
                                    holidayCount += 1
                                    holiday = stuff[1:]
                                    if(holidayCount == 1):
                                        if(holiday == 'Halloween'):
                                            holiday_color = 0x8650AC
                                            holiday_thumb = 'https://wiki.teamfortress.com/w/images/6/6d/Backpack_Horseless_Headless_Horsemann%27s_Head.png'
                                        else:
                                            holiday_color = 0xe3442b
                                            holiday_thumb = 'https://wiki.teamfortress.com/w/images/6/65/Backpack_Smissmas_2015_Festive_Gift.png'
                                    else:
                                        holiday_color = tf2_color
                                        holiday = ''
                                        holiday_thumb = tf2_icon
                                    #print(holiday)
                                elif(stuff[1:] == 'Unusual Effect'):
                                    if(isCollection is False):
                                        item_type = stuff[1:]
                                    merc = ""
                                    #print(item_type)
                                elif(stuff[1:] == 'War Paint'):
                                    if(isCollection is False):
                                        item_type = stuff[1:]
                                    merc = ""
                                    #print(item_type)

                        # GAMEMODE TAGS (FOR MAPS)
                        if (tagz.startswith("Game Mode:")):
                            #print(tagz) #DEBUG
                            if(len(item_type) != 'Collection'):
                                item_type = 'Map'

                            others = tagz.split(":")[1]
                            others = others.split(',')
                            #print(others) # DEBUG
                            for stuff in others:
                                #print(stuff)
                                if(stuff[1:] != 'Specialty'):
                                    game_type = stuff[1:]


                    #CONTRIBUTOR EXTRACTION
                    if(isCollection): # As of 5/20/2020, collection pages use the same class names as item pages.

                        # Adding a check here to ask if the collection in question is a personal one or for an item set.
                        hasRespondedValidly = False

                        while (hasRespondedValidly == False):
                            msg = await ctx.author.send('**It seems that you are submitting a collection. Is this collection an item set? (Y/N)**')
                            yn = await client.wait_for('message', check=check)
                            
                            if len(yn.content) > 0:
                                if yn.content.lower() in valid_yes:
                                    isPersonal = False
                                else:
                                    isPersonal = True
                                hasRespondedValidly = True
                            else:
                                isPersonal = False

                        #print("Exited Y/N loop")
                        if (isPersonal == False):
                            #print("ISN'T PERSONAL")
                            # Opening page of first cosmetic of collection to grab all contributor names.
                            urlHUB = soup.find('div', class_= 'clearfix collection')
                            urlHUB = urlHUB.find_all('div', class_= 'collectionItemDetails', attrs = 'href')[0]

                            itemLink = urlHUB.find('a', href = True)['href']

                            # Now that we have the item link, we begin extracting the names.
                            page = urllib.request.urlopen(itemLink)
                            soup = bs.BeautifulSoup(page, 'lxml')

                        contribBlock = soup.find('div', class_= 'creatorsBlock')
                        contribArr = []

                        for contribs in contribBlock.find_all('div', class_='friendBlockContent'):
                            contribText = contribs.text.split('             ')[0]
                            contribText = contribText.split('\t')
                            contribText = contribText[4]
                            contribText = contribText.split('\n')[0]

                            contribArr.append(contribText)                           
                    else:
                        #print("IS PERSONAL")
                        contribBlock = soup.find('div', class_= 'creatorsBlock')

                        contribArr = []
                        for contribs in contribBlock.find_all('div', class_='friendBlockContent'):
                            contribText = contribs.text.split('             ')[0]
                            contribText = contribText.split('\t')
                            contribText = contribText[4]
                            contribText = contribText.split('\n')[0]

                            contribArr.append(contribText)

                    contrib_str = ""
                    #print(len(contribArr))
                    num_contribs = 0
                    for contributor in contribArr:
                        #print(contributor)
                        contrib_str = contrib_str + contributor
                        if(num_contribs + 1 < len(contribArr)):
                            contrib_str = contrib_str + ", "
                        num_contribs = num_contribs + 1
                    #print(curr_step)

            # ARTWORK UPLOAD
            if(curr_step == 1):
                #print("Currently in image submission step.")
                #print(title.split(':'))
                #print(soup)

                msg = await ctx.author.send('**Now let\'s get your artwork. It can either be a direct upload or link.**\nImages must be under 3mb in order to be posted on Twitter.')
                img = await client.wait_for('message', check=check)
                if (img.content.lower().startswith('restart')):
                    curr_step = -1
                elif(img.content.lower().startswith('cancel')):
                    curr_step = 6
                    canceled = True
                elif (len(img.attachments) == 0):
                    if(img.content.startswith('https://') or img.content.startswith('www.') or img.content.startswith('cdn') or img.content.beginswith('https://cdn.discordapp.com/attachments/')):
                        #if(validate_web_url(img.content) is True):
                        img = img.content
                        curr_step = curr_step + 1
                    # else:
                    #     print('Invalid link received.')
                    #     await ctx.author.send('**Invalid link**')
                else:
                    img = img.attachments[0].url
                    curr_step = curr_step + 1

            if (curr_step == 2):
                #print("KritzKast Promo Stage!")
                if(item_type == 'War Paint' or item_type == 'Unusual Effect' or item_type == ''):
                    curr_step = curr_step + 1
                else:
                    msg = await ctx.author.send('We are proud to announce that we are now partnered with KritzKast!\n**Would you like to allow KritzKast to use this artwork for thumbnails in future videos/events? (Y/N)**\nItems whose renders are used will be linked wherever used. All contributors of the item will also receive a **Unique Lo-Fi Longwave**.')
                    kk_yn = await client.wait_for('message', check=check)
                    if kk_yn.content.lower() in valid_yes:
                        kk_approved = True
                    elif (kk_yn.content.lower().startswith('restart')):
                        curr_step = 0
                    elif(kk_yn.content.lower().startswith('cancel')):
                        curr_step = 6
                        canceled = True

                    curr_step = curr_step + 1

            if (curr_step == 3):
                #print("Currently in embed review step.")

                desc = ""
                if(len(item_type) == 0):
                    item_type = "Community Submission"

                if(len(game_type) > 0):
                    desc = desc + holiday + " " + game_type + " " + item_type 
                elif(len(holiday) > 0 and len(merc) > 0):
                    if(merc == "All-Class" or merc == "Multi-Class"):
                        desc = desc + merc + " " + holiday + " " + item_type
                    else:
                        desc = desc + holiday + " " + merc  + " " + item_type
                elif(len(holiday) > 0 and len(merc) == 0):
                    desc = desc + holiday + " " + item_type
                elif(len(holiday) == 0 and len(merc) > 0):
                    desc = desc + merc + " " + item_type
                else:
                    desc = item_type
                direct_link = "steam://url/communityfilepage/"
                direct_link = direct_link + item_id

                msg = await ctx.author.send('**Alright, does this look good? (Y/N)**')
                # CODE TO PRODUCE EMBEDDED MESSAGE HERE!
                embed = discord.Embed(
                    title = name,
                    url = link,
                    description = desc,
                    colour = holiday_color
                )
                #embed.set_footer(text = 'This is a footer.')
                embed.set_image(url = img)
                # urllib.request.urlretrieve(img, "./files/thumb.jpg")
                if(isTF2 is True):
                    embed.set_thumbnail(url = holiday_thumb)
                #embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
                if(len(contribs) > 0):
                    if(isCollection is True):
                        embed.add_field(name = 'Created by', value = contrib_str, inline = False)                        
                    else:
                        embed.add_field(name = 'Created by', value = contrib_str, inline = False)
                embed.add_field(name = 'Open in Steam', value = direct_link, inline = False)
                #embed.add_field(name = 'Field Name', value = 'Field Value', inline = True)

                await ctx.author.send(embed = embed)
                yn = await client.wait_for('message', check=check)
                if yn.content.lower() in valid_yes:
                    await ctx.author.send('**Submitting!**')
                    imgLink = img
                    curr_step = curr_step + 1
                elif (yn.content.lower().startswith('restart')):
                    curr_step = 0
                elif(yn.content.lower().startswith('cancel')):
                    curr_step = 6
                    canceled = True
                else:
                    msg = await ctx.author.send('**Do you want to start over? (Y/N)**')
                    yn1 = await client.wait_for('message', check=check)
                    if yn1.content.lower() in valid_yes:
                        curr_step = 0
                    else:
                        canceled = True
                        curr_step = curr_step + 1

        if(canceled is True):
            msg = await ctx.author.send('**Item submission process canceled. To restart type *.release* or *.submit* in #discussions.**')
        else:
            # POSTING TO DISCORD CHANNEL
            # releases
            channel = client.get_channel(None)
            await channel.send(embed = embed) # SENDS EMBED TO RELEASES
            # discussion
            channel = client.get_channel(None)
            await channel.send(embed = embed) # SENDS EMBED TO DISCUSSION
            if(isTF2 is True and isPersonal == False):
                #print('Sending to approval queue!')
                channel = client.get_channel(None)
                if(kk_approved == False):
                    await channel.send('Pending item approval! @here', embed = embed) # SENDS EMBED TO APPROVAL
                else:
                    await channel.send('Pending item approval! @here [APPROVED FOR KRITZKAST]', embed = embed) # SENDS EMBED TO APPROVAL
    #msg = await ctx.author.send('embed code here')


client.run(discord_key)
