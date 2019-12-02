import discord
#import aiohttp
import bs4 as bs
import urllib.request
from discord.ext import commands, tasks

client = commands.Bot(command_prefix = '.')


@client.event
async def on_ready():
	await client.change_presence(status=discord.Status.online, activity=discord.Game('Use .help for more info!'))
	print('Bot is ready!')

@client.event
async def on_member_join(member):
	print(f'{member} has joined a server.')

@client.event
async def on_member_remove(member):
	print(f'{member} has left a server.')

@client.command(aliases = ['release', 'submit'])
async def _release(ctx): #something like (ctx *, name) would just mean it ignores all the text
	#await delete(command, delay=None)
	print(f'{ctx.author} has attempted submitting an item')
	curr_step = 0
	num_contribs = 0
	contribs = []
	canceled = False
	await ctx.channel.purge(limit = 1)
	msg = await ctx.author.send('Hello! It seems you are trying to submit an item. To restart the process at any time, type *restart*. To cancel the process, just type *cancel*.\nIf I stop responding at any point just start over and type *.submit* or *.release* in #discussions.')

	# STEPS
	while(curr_step < 4):

		def check(message):
			return message.author == ctx.author and message.channel == msg.channel

		# LINK INPUT
		if(curr_step == 0):
			valid_link = False
			msg = await ctx.author.send('First let me have your item\'s Steam Workshop link.')
			#https://steamcommunity.com/sharedfiles/filedetails/?id=1924815269
			while(valid_link is False):
				link = await client.wait_for('message', check=check)
				if (link.content.startswith('https://steamcommunity.com/sharedfiles/filedetails/?id=') or link.content.startswith('https://www.steamcommunity.com/sharedfiles/filedetails/?id=')
					or link.content.startswith('www.steamcommunity.com/sharedfiles/filedetails/?id=') or link.content.startswith('steamcommunity.com/sharedfiles/filedetails/?id=')
					or link.content.startswith('restart') or link.content.startswith('Restart') or link.content.startswith('cancel') or link.content.startswith('Cancel')):
				#await name.channel.send(f'{link.content} received!')
					link = link.content
					valid_link = True
				if(valid_link is False):
					msg = await ctx.author.send('Oops! It seems your link isn\'t one from Steam Community. Please make sure your link is valid.')
					
			if (link.startswith('restart') or link.startswith('Restart')):
				curr_step = 0
			elif(link.startswith('cancel') or link.startswith('Cancel')):
				curr_step = 6
				canceled = True
			else:
				item_id = link.split('=')[1]
				curr_step = curr_step + 1

				# Web scrubbing junk
				page = urllib.request.urlopen(link)
				soup = bs.BeautifulSoup(page, 'lxml')
				title = soup.find('div', class_= 'workshopItemTitle')
				print(title) #DEBUG
				name = title.text
				print(name) #DEBUG
				tags = soup.find('div', class_= 'col_right')
				tagArr = []
				for ptag in tags.find_all('div', class_='workshopTags'):
				    # prints the p tag content
				    tagArr.append(ptag.text)

				holiday = ""
				merc = ""
				item_type = ""
				for tagz in tagArr:
					if (tagz.startswith("Class:")):
						print(tagz) #DEBUG
						people = tagz.split(":")[1][1:]
						print(slot) #DEBUG
						mercs = people.split(',')
						if(len(mercs) == 1):
							merc = mercs
						else:
							if(len(mercs) < 9):
								merc = "Multi-Class"
							else:
								merc = "All-Class"


				if (tagz.startswith("Slot:")):
					# ITEM TYPE EXTRACTION
					print(tagz) #DEBUG
					slot = tagz.split(":")[1][1:]
					print(slot) #DEBUG

					if(len(slot.split(",")) > 1):
						slot = slot.split(",")[0]
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
							print(holiday)
						elif(stuff[1:] == 'Unusual Effect'):
							item_type = stuff[1:]
							merc = ""
							print(item_type)
						elif(stuff[1:] == 'War Paint'):
							item_type = stuff[1:]
							merc = ""
							print(item_type)

		# ARTWORK UPLOAD
		if(curr_step == 1):

			#print(title.split(':'))
			#print(soup)

			msg = await ctx.author.send('Awesome! Now let\'s get your artwork. It can either be a direct upload or link.')
			img = await client.wait_for('message', check=check)
			if (img.content.startswith('restart') or img.content.startswith('Restart')):
				curr_step = -1
			elif(img.content.startswith('cancel') or img.content.startswith('Cancel')):
				curr_step = 6
				canceled = True
			elif (len(img.attachments) == 0):
				img = img.content
				curr_step = curr_step + 1
			else:
				img = img.attachments[0].url
				curr_step = curr_step + 1

		# CONTRIBUTORS GRAB
		if(curr_step == 2):
			msg = await ctx.author.send('Almost done! Would you like to add any other contributors to this post? (Y/N)')
			#def check_yn(message):
				## CURRENT ISSUE!!! Code breaks if non y/n input given.
				#return (message.content == 'Y' or message.content == 'y' or message.content == 'N' or message.content == 'n') and message.author == ctx.author and message.channel == msg.channel
			yn = await client.wait_for('message', check=check)
			if (yn.content.startswith('restart') or yn.content.startswith('Restart')):
				curr_step = -1
			elif(yn.content.startswith('cancel') or yn.content.startswith('Cancel')):
				curr_step = 6
				canceled = True
			elif(yn.content == 'Y' or yn.content == 'y'):
				#has_contribs = True
				msg = await ctx.author.send('Cool! Add each contributor **individually** and type *Done* when you\'re finished.')
				hmm = True
				while(hmm is True):
					contrib = await client.wait_for('message', check=check)
					if(contrib.content == 'Done' or contrib.content == 'done'):
						hmm = False
					else:
						contribs.append(contrib.content)
						num_contribs = num_contribs + 1
						await ctx.author.send(f'Contributor {contrib.content} appended to submission. This item currently has {num_contribs + 1} total contributors.')

				contrib_str = ""
				while(num_contribs != 0):
					contrib_str = contrib_str + contribs[num_contribs - 1]
					if(num_contribs > 1):
						contrib_str = contrib_str + ", "
					num_contribs = num_contribs - 1
			curr_step = curr_step + 1

		if (curr_step == 3):
			desc = ""
			if(len(item_type) == 0):
				item_type = "Community Submission"

			if(len(holiday) > 0 and len(merc) > 0):
				desc = desc + merc + " " + holiday + " " + item_type
			elif(len(holiday) > 0 and len(merc) == 0):
				desc = desc + holiday + " " + item_type
			elif(len(holiday) == 0 and len(merc) > 0):
				desc = desc + merc + " " + item_type
			else:
				desc = item_type
			direct_link = "steam://url/communityfilepage/"
			direct_link = direct_link + item_id

			msg = await ctx.author.send('Alright, does this look good? (Y/N)')
			# CODE TO PRODUCE EMBEDDED MESSAGE HERE!
			embed = discord.Embed(
				title = name,
				url = link,
				description = desc,
				colour = 0xc35108
			)
			#embed.set_footer(text = 'This is a footer.')
			embed.set_image(url = img)
			#embed.set_thumbnail(url = 'https://wiki.teamfortress.com/w/images/thumb/1/13/Icon_scout.jpg/150px-Icon_scout.jpg')
			embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
			if(len(contribs) > 0):
				embed.add_field(name = 'Co-Contributors', value = contrib_str, inline = False)
			embed.add_field(name = 'Open in Steam', value = direct_link, inline = False)
			#embed.add_field(name = 'Field Name', value = 'Field Value', inline = True)

			await ctx.author.send(embed = embed)
			yn = await client.wait_for('message', check=check)
			if (yn.content.startswith('restart') or yn.content.startswith('Restart')):
				curr_step = 0
			elif(yn.content.startswith('cancel') or yn.content.startswith('Cancel')):
				curr_step = 6
				canceled = True
			elif(yn.content == 'Y' or yn.content == 'y'):
				await ctx.author.send('Submitting!')
				curr_step = curr_step + 1
			else:
				msg = await ctx.author.send('Do you want to start over? (Y/N)')
				yn1 = await client.wait_for('message', check=check)
				if(yn1.content == 'Y' or yn1.content == 'y'):
					curr_step = 0
				else:
					canceled = True
					curr_step = curr_step + 1

	if(canceled is True):
		msg = await ctx.author.send('Item submission process canceled. To restart type *.release* or *.submit* in #discussions.')
	else:
		channel = client.get_channel(650459986178080798)
		await channel.send(embed = embed)

	#msg = await ctx.author.send('embed code here')


# @client.command
# async def timeleft(ctx, secs):
# 	await ctx.channel.purge(limit = 1)
# 	if (secs != 0):
# 		await ctx.send(f'Time Left: {secs}')
# 	else:
# 		await ctx.send('The countdown has ended!')

# @client.event
# async def on_message(message):
#     if message.content.startswith('obunga'):
#         channel = message.channel
#         await channel.send('Haha funny!')

#         def check(m):
#             return m.content == 'hello' and m.channel == channel

#         msg = await client.wait_for('message', check=check)
#         await channel.send('Hello {.author}!'.format(msg))

client.run('NjUwNDQ2NTg1MzI2NjAwMjEy.XeLg4w.wQHxj68SZshGrxB4j7Qu7Jv19Cg')

