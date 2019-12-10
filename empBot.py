import discord
import tweepy
import aiohttp
import asyncio
import os
import bs4 as bs
import urllib.request
from urllib.request import urlopen, URLError
from discord.ext import commands, tasks

# Emporium Bot v1 (Build Date: 12/4/2019)
# Coded by rabscootle#1988 (Andres Signoret)

def validate_web_url(url="http://google"):
    try:
        urlopen(url)
        return True
    except URLError:
        return False

client = commands.Bot(command_prefix = ['.', '!'])
client.remove_command('help')

# TWITTER KEYS
consumer_key = None
consumer_secret = None
access_token = None
access_token_secret = None

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

async def tweet(image, message):
    api.update_with_media(image, status = message)
    os.remove(image)

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Use .empinfo!'))
    channel = client.get_channel(None)
    await channel.send('I am live!') # SENDS EMBED TO RELEASES
    print('Bot is ready!')

@client.event
async def on_member_join(member):
    print(f'{member} has joined a server.')

@client.event
async def on_member_remove(member):
    print(f'{member} has left a server.')

@client.event
async def on_reaction_add(reaction, user):
    print(reaction.message.content)
    channel = reaction.message.channel
    print(str(reaction.emoji))
    if(reaction.message.channel.name == "approval" and str(reaction.emoji) == '<:engythumb:468840724830355476>' and reaction.count == 1 and (len(reaction.message.content) < 6)):
        embedMsg = reaction.message.embeds[0]
        subType = embedMsg.description
        itemName = embedMsg.title
        itemURL = embedMsg.url

        # TWITTER
        imgURL = embedMsg.image.url
            # Downloading images.
        loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession(loop=loop) as session:
            image = await fetch_img(session,imgURL)
        with open("img.png", "wb") as f:
            f.write(image)
        tweetMessage = "New " + subType + ", " + itemName + "! Vote now on Steam Workshop: " + itemURL + " #TF2"
        await tweet('img.png', tweetMessage)
        await reaction.message.delete() #deletes mesage from page (removed)
        approvedStr = ""
        approvedStr = approvedStr + itemName + " has been approved for Twitter release by " + user.name + "!"
        await channel.send(approvedStr, embed = embedMsg)

@client.command()
async def empinfo(ctx):
    #print(f'{ctx.author} has attempted submitting an item')
    await ctx.channel.purge(limit = 1)
    msg = await ctx.author.send('To submit an item to #releases and the TF2 Emporium Twitter (@TF2Emporium), type .release or .submit in #discussion.\nPlease note your item may take some time to appear on the Twitter as each submission is manually approved by staff members.')

@client.command(aliases = ['release', 'submit'])
async def _release(ctx): #something like (ctx *, name) would just mean it ignores all the text
    #await delete(command, delay=None)
    if(ctx.channel.name == "discussion"):
        print(f'{ctx.author} has attempted submitting an item')
        curr_step = 0
        num_contribs = 0
        contribs = []
        canceled = False
        await ctx.channel.purge(limit = 1)
        #imgLink = ""
        msg = await ctx.author.send('Hello! It seems you are trying to submit an item. To restart the process at any time, type *restart*. To cancel the process, just type *cancel*.\nIf I stop responding at any point just start over and type *.submit* or *.release* in #discussions.\nIf multiple instances of me begin to exist, just type *cancel* and restart the process.\n\n')
        #tweetMessage = ""
        isTF2 = False
        isCollection = False

        # STEPS
        while(curr_step < 3):

            def check(message):
                return message.author == ctx.author and message.channel == msg.channel

            # LINK INPUT
            if(curr_step == 0):
                print("Currently in link submission step.")
                valid_link = False
                isTF2 = False
                isCollection = False
                holiday_color = 0xB98A2E
                holiday_thumb = 'https://wiki.teamfortress.com/w/images/b/be/TF2_crosshair_orange.png'
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
                        print('TF2 Submission Detected!')
                    else:
                        holiday = game
                        holiday_color = 0x484e6b

                    #Name Extraction
                    title = soup.find('div', class_= 'workshopItemTitle')
                    print(title) #DEBUG
                    name = title.text
                    print(name) #DEBUG
                    
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
                            print(tagz) #DEBUG
                            people = tagz.split(":")[1][1:]
                            print(people) #DEBUG
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
                            print(tagz) #DEBUG
                            slot = tagz.split(":")[1][1:]
                            print(slot) #DEBUG

                            if(len(slot.split(",")) > 1):
                                slot = 'Cosmetic'
                            if(len(item_type) == 0):
                                item_type = slot
                            print(item_type) #DEBUG

                        # OTHER TAGS
                        if (tagz.startswith("Other:")):
                            print(tagz) #DEBUG

                            others = tagz.split(":")[1]
                            others = others.split(',')
                            print(others) # DEBUG
                            for stuff in others:
                                #print(stuff)
                                if(stuff[1:] == 'Halloween' or stuff[1:] == 'Smissmas'):
                                    holiday = stuff[1:]
                                    if(holiday == 'Halloween'):
                                        holiday_color = 0x8650AC
                                        holiday_thumb = 'https://wiki.teamfortress.com/w/images/6/6d/Backpack_Horseless_Headless_Horsemann%27s_Head.png'
                                    else:
                                        holiday_color = 0xe3442b
                                        holiday_thumb = 'https://wiki.teamfortress.com/w/images/6/65/Backpack_Smissmas_2015_Festive_Gift.png'
                                    print(holiday)
                                elif(stuff[1:] == 'Unusual Effect'):
                                    if(isCollection is False):
                                        item_type = stuff[1:]
                                    merc = ""
                                    print(item_type)
                                elif(stuff[1:] == 'War Paint'):
                                    if(isCollection is False):
                                        item_type = stuff[1:]
                                    merc = ""
                                    print(item_type)

                        # GAMEMODE TAGS (FOR MAPS)
                        if (tagz.startswith("Game Mode:")):
                            print(tagz) #DEBUG
                            if(len(item_type) != 'Collection'):
                                item_type = 'Map'

                            others = tagz.split(":")[1]
                            others = others.split(',')
                            print(others) # DEBUG
                            for stuff in others:
                                #print(stuff)
                                if(stuff[1:] != 'Specialty'):
                                    game_type = stuff[1:]


                    #CONTRIBUTOR EXTRACTION
                    if(item_type == 'Collection'):
                        contribBlock = soup.find('div', class_= 'creatorsBlock')
                        #print(contribBlock) #DEBUG
                        #print(contribBlock.text) #DEBUG
                        contribArr = []
                        for contribs in contribBlock.find_all('div', class_='linkAuthor'):
                            #print(contribs.text.split('\n')[0])
                            contribText = contribs.text
                            contribArr.append(contribText)                        
                    else:
                        contribBlock = soup.find('div', class_= 'creatorsBlock')
                        #print(contribBlock) #DEBUG
                        #print(contribBlock.text) #DEBUG
                        contribArr = []
                        for contribs in contribBlock.find_all('div', class_='friendBlockContent'):
                            #print(contribs.text.split('\n')[0])
                            contribText = contribs.text.split('             ')[0]
                            #print(contribText) #DEBUG
                            contribText = contribText.split('\t')
                            contribText = contribText[4]
                            contribText = contribText.split('\n')[0]
                            #print(contribText) #DEBUG
                            #print(contribText)

                            contribArr.append(contribText)

                    contrib_str = ""
                    print(len(contribArr))
                    num_contribs = 0
                    for contributor in contribArr:
                        print(contributor)
                        contrib_str = contrib_str + contributor
                        if(num_contribs + 1 < len(contribArr)):
                            contrib_str = contrib_str + ", "
                        num_contribs = num_contribs + 1

            # ARTWORK UPLOAD
            if(curr_step == 1):
                print("Currently in image submission step.")
                #print(title.split(':'))
                #print(soup)

                msg = await ctx.author.send('**Awesome! Now let\'s get your artwork. It can either be a direct upload or link.\nImages must be under 3mb in order to be posted on Twitter.**')
                img = await client.wait_for('message', check=check)
                if (img.content.startswith('restart') or img.content.startswith('Restart')):
                    curr_step = -1
                elif(img.content.startswith('cancel') or img.content.startswith('Cancel')):
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
                print("Currently in embed review step.")

                desc = ""
                if(len(item_type) == 0):
                    item_type = "Community Submission"

                if(len(game_type) > 0):
                    desc = desc + holiday + " " + game_type + " " + item_type 
                elif(len(holiday) > 0 and len(merc) > 0):
                    desc = desc + merc + " " + holiday + " " + item_type
                elif(len(holiday) > 0 and len(merc) == 0):
                    desc = desc + holiday + " " + item_type
                elif(len(holiday) == 0 and len(merc) > 0):
                    desc = desc + merc + " " + item_type
                else:
                    desc = item_type
                direct_link = "steam://url/communityfilepage/"
                direct_link = direct_link + item_id

                # TWEET GENERATION (OLD)
                # tweetMessage = tweetMessage + "New "
                # if(len(holiday) > 0):
                #     tweetMessage = tweetMessage + holiday + " "
                # if(len(merc) > 0):
                #     tweetMessage = tweetMessage + merc + " "
                # tweetMessage = tweetMessage + item_type + ", " + name
                # if(len(game_type) > 0):
                #     tweetMessage = tweetMessage + " (" + game_type + ")"
                # tweetMessage = tweetMessage + "! Vote now on Steam Workshop: " + link + " #TF2"
                # print(tweetMessage)

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
                        embed.add_field(name = 'Published by', value = contrib_str, inline = False)                        
                    else:
                        embed.add_field(name = 'Created by', value = contrib_str, inline = False)
                embed.add_field(name = 'Open in Steam', value = direct_link, inline = False)
                #embed.add_field(name = 'Field Name', value = 'Field Value', inline = True)

                await ctx.author.send(embed = embed)
                yn = await client.wait_for('message', check=check)
                if (yn.content.startswith('restart') or yn.content.startswith('Restart')):
                    curr_step = 0
                elif(yn.content.startswith('cancel') or yn.content.startswith('Cancel')):
                    curr_step = 6
                    canceled = True
                elif(yn.content == 'Y' or yn.content == 'y' or yn.content == 'Yes' or yn.content == 'yes'):
                    await ctx.author.send('**Submitting!**')
                    imgLink = img
                    curr_step = curr_step + 1
                else:
                    msg = await ctx.author.send('**Do you want to start over? (Y/N)**')
                    yn1 = await client.wait_for('message', check=check)
                    if(yn1.content == 'Y' or yn1.content == 'y' or yn1.content == 'Yes' or yn1.content == 'yes'):
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
            if(isTF2 is True):
                print('Sending to approval queue!')
                channel = client.get_channel(None)
                await channel.send('@here', embed = embed) # SENDS EMBED TO APPROVAL
    #msg = await ctx.author.send('embed code here')

client.run(None)
