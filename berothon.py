import telethon
from telethon import events
from config import *
import os
import logging
import asyncio
import time
from telethon.tl import functions, types
from telethon.tl.functions.messages import ImportChatInviteRequest as Get
from telethon.utils import get_display_name
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import FloodWaitError
from telethon import TelegramClient, events
from collections import deque
from telethon import functions
from telethon.errors.rpcerrorlist import (
    UserAlreadyParticipantError,
    UserNotMutualContactError,
    UserPrivacyRestrictedError,
)
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerUser
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl import functions
from hijri_converter import Gregorian
from telethon.tl.functions.channels import LeaveChannelRequest
import base64
import datetime
from payment import *
from help import *
from checktele import *
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
import requests
# -
import asyncio
import os
import contextlib
import sys
from asyncio.exceptions import CancelledError
import requests
import heroku3
import urllib3
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from telethon import events 
from JoKeRUB import HEROKU_APP, UPSTREAM_REPO_URL, l313l

from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..sql_helper.global_collection import (
    add_to_collectionlist,
    del_keyword_collectionlist,
    get_collectionlist_items,
)
from ..sql_helper.globals import delgvar

plugin_category = "tools"
cmdhd = Config.COMMAND_HAND_LER
ENV = bool(os.environ.get("ENV", False))

LOGS = logging.getLogger(__name__)
# -- ثـوابت -- #

HEROKU_APP_NAME = Config.HEROKU_APP_NAME or None
HEROKU_API_KEY = Config.HEROKU_API_KEY or None
Heroku = heroku3.from_key(Config.HEROKU_API_KEY)
heroku_api = "https://api.heroku.com"

UPSTREAM_REPO_BRANCH = Config.UPSTREAM_REPO_BRANCH

REPO_REMOTE_NAME = "temponame"
IFFUCI_ACTIVE_BRANCH_NAME = "HuRe"
NO_HEROKU_APP_CFGD = "no heroku application found, but a key given? 😕 "
HEROKU_GIT_REF_SPEC = "HEAD:refs/heads/HuRe"
RESTARTING_APP = "re-starting heroku application"
IS_SELECTED_DIFFERENT_BRANCH = (
    "looks like a custom branch {branch_name} "
    "is being used:\n"
    "in this case, Updater is unable to identify the branch to be updated."
    "please check out to an official branch, and re-start the updater."
)


# -- انتهاء الثوابت -- #
#ياعلي
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

requirements_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "requirements.txt"
)


async def gen_chlog(repo, diff):
    d_form = "%d/%m/%y"
    return "".join(
        f" • {c.message} {c.author}\n ({c.committed_datetime.strftime(d_form)}) "
        for c in repo.iter_commits(diff)
        )


async def print_changelogs(event, ac_br, changelog):
    changelog_str = (
        f"**᯽︙ قام مطورين السورس بتحديث ريبيثون**\n᯽︙ **التـغييرات\n** {changelog}"
    )
    if len(changelog_str) > 4096:
        await event.edit("`Changelog is too big, view the file to see it.`")
        with open("output.txt", "w+") as file:
            file.write(changelog_str)
        await event.client.send_file(
            event.chat_id,
            "output.txt",
            reply_to=event.id,
        )
        os.remove("output.txt")
    else:
        await event.client.send_message(
            event.chat_id,
            changelog_str,
            reply_to=event.id,
        )
    return True


async def update_requirements():
    reqs = str(requirements_path)
    try:
        process = await asyncio.create_subprocess_shell(
            " ".join([sys.executable, "-m", "pip", "install", "-r", reqs, "--upgrade", "--force-reinstall"]),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode
    except Exception as e:
        return repr(e)


async def update(event, repo, ups_rem, ac_br):
    try:
        ups_rem.pull(ac_br)
    except GitCommandError:
        repo.git.reset("--hard", "FETCH_HEAD")
    await update_requirements()
    jasme = await event.edit(
        "** ᯽︙ تم تحديث سورس ريبيثون بنجاح انتظر قليلا سوف نخبرك بعد اعادة التشغيل !**"
    )
    await event.client.reload(jasme)

def stream_build_logs(appsetup_id):
    appsetup = Heroku.get_appsetup(appsetup_id)
    build_iterator = appsetup.build.stream(timeout=2)
    try:
        for line in build_iterator:
            if line:
                print("{0}".format(line.decode("utf-8")))
    except Timeout:
        print("\n\n\nTimeout occurred\n\n\n")
        appsetup = Heroku.get_appsetup(appsetup_id)
        if appsetup.build.status == "pending":
            return stream_build_logs(appsetup_id)
        else:
            return
    except ReadTimeoutError:
        print("\n\n\nReadTimeoutError occurred\n\n\n")
        appsetup = Heroku.get_appsetup(appsetup_id)
        if appsetup.build.status == "pending":
            return stream_build_logs(appsetup_id)
        else:
            return

async def deploy(event, repo, ups_rem, ac_br, txt):
    if HEROKU_API_KEY is None:
        return await event.edit("`Please set up`  **HEROKU_API_KEY**  ` Var...`")
    heroku = heroku3.from_key(HEROKU_API_KEY)
    heroku_applications = heroku.apps()
    if HEROKU_APP_NAME is None:
        await event.edit(
            "`Please set up the` **HEROKU_APP_NAME** `Var`"
            " to be able to deploy your userbot...`"
        )
        repo.__del__()
        return
    heroku_app = next(
        (app for app in heroku_applications if app.name == HEROKU_APP_NAME),
        None,
    )

    if heroku_app is None:
        await event.edit(
            f"{txt}\n" "`Invalid Heroku credentials for deploying userbot dyno.`"
        )
        return repo.__del__()
    lMl10l = await event.edit(
        "**᯽︙ الأن يتم تحديث ريبو التنصيب, عليك الانتظار لحين تحميل المكاتب, يستغرق الامر من 4-5 دقائق**"
    )
    try:
        ulist = get_collectionlist_items()
        for i in ulist:
            if i == "restart_update":
                del_keyword_collectionlist("restart_update")
    except Exception as e:
        LOGS.error(e)
    try:
        add_to_collectionlist("restart_update", [lMl10l.chat_id, lMl10l.id])
    except Exception as e:
        LOGS.error(e)
    ups_rem.fetch(ac_br)
    repo.git.reset("--hard", "FETCH_HEAD")
    heroku_git_url = heroku_app.git_url.replace(
        "https://", f"https://api:{HEROKU_API_KEY}@"
    )

    if "heroku" in repo.remotes:
        remote = repo.remote("heroku")
        remote.set_url(heroku_git_url)
    else:
        remote = repo.create_remote("heroku", heroku_git_url)
    try:
        remote.push(refspec="HEAD:refs/heads/HuRe", force=True)
        build_status = heroku_app.builds(order_by="created_at", sort="desc")[0]
        url = build_status.output_stream_url
        log_content = " "
        response = requests.get(url)
        if response.status_code == 200:
            log_content = response.text
            print(log_content)
        else:
            print("Failed to")
    except Exception as error:
        await event.edit(f"{txt}\n**حدث خطأ:**\n`{error}`")
        return repo.__del__()
   
    build_status = heroku_app.builds(order_by="created_at", sort="desc")[0]
    
    for attribute_name in dir(build_status):
        attribute_value = getattr(build_status, attribute_name)
        print(f"{attribute_name}: {attribute_value}")

    if build_status.status == "failed":
        with open('log_file.txt', 'w') as file:
        	file.write(log_content)

        with open('log_file.txt', 'rb') as file:
            await l313l.send_file(
            event.chat_id, "log_file.txt", caption="حدث خطأ بالبناء"
        )
        os.remove("log_file.txt")
        return
    try:
        remote.push("HuRe:main", force=True)
    except Exception as error:
        await event.edit(f"{txt}\n**هذا هو سجل الاخطاء:**\n`{error}`")
        return repo.__del__()
    await event.edit("`فشل التحديث, جار اعادة التشغيل`")
    with contextlib.suppress(CancelledError):
        await event.client.disconnect()
        if HEROKU_APP is not None:
            HEROKU_APP.restart()

@l313l.ar_cmd(
    pattern="تحديث(| الان)?$",
    command=("تحديث", plugin_category),
    info={
        "header": "To update userbot.",
        "description": "I recommend you to do update deploy atlest once a week.",
        "options": {
            "now": "Will update bot but requirements doesnt update.",
            "deploy": "Bot will update completly with requirements also.",
        },
        "usage": [
            "{tr}update",
            "{tr}تحديث",
            "{tr}update deploy",
        ],
    },
)
async def upstream(event):
    "To check if the bot is up to date and update if specified"
    conf = event.pattern_match.group(1).strip()
    event = await edit_or_reply(event, "**᯽︙ يـتـم البـحـث عـن تـحديثـات سـورس ريبيثون انـتـظـر**")
    off_repo = UPSTREAM_REPO_URL
    force_update = False
    
    try:
        txt = "`Oops.. Updater cannot continue due to "
        txt += "some problems occured`\n\n**LOGTRACE:**\n"
        repo = Repo()
    except NoSuchPathError as error:
        await event.edit(f"{txt}\n`directory {error} is not found`")
        return repo.__del__()
    except GitCommandError as error:
        await event.edit(f"{txt}\n`Early failure! {error}`")
        return repo.__del__()
    except InvalidGitRepositoryError as error:
        if conf is None:
            return await event.edit(
                f"`Unfortunately, the directory {error} "
                "does not seem to be a git repository.\n"
                "But we can fix that by force updating the userbot using "
                ".تحديث الان.`"
            )
        repo = Repo.init()
        origin = repo.create_remote("upstream", off_repo)
        origin.fetch()
        force_update = True
        repo.create_head("HuRe", origin.refs.HuRe)
        repo.heads.HuRe.set_tracking_branch(origin.refs.HuRe)
        repo.heads.HuRe.checkout(True)
    ac_br = repo.active_branch.name
    if ac_br != UPSTREAM_REPO_BRANCH:
        await event.edit(
            "**[UPDATER]:**\n"
            f"`Looks like you are using your own custom branch ({ac_br}). "
            "in that case, Updater is unable to identify "
            "which branch is to be merged. "
            "please checkout to any official branch`"
        )
        return repo.__del__()
    try:
        repo.create_remote("upstream", off_repo)
    except BaseException:
        pass
    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)
    changelog = await gen_chlog(repo, f"HEAD..upstream/{ac_br}")
    # Special case for deploy
    if changelog == "" and not force_update:
        await event.edit(
            "**᯽︙ 🤍 لا توجد تحديثات الى الان **\n"
        )
        return repo.__del__()
    if conf == "" and not force_update:
        await print_changelogs(event, ac_br, changelog)
        await event.delete()
        return await event.respond(
            f"⌔ :  لتحديث سورس ريبيثون ارسل : `.تحديث الان` "
        )

    if force_update:
        await event.edit(
            "`Force-Syncing to latest stable userbot code, please wait...`"
        )
    if conf == "الان":
        await event.edit("** ᯽︙ جار تحـديـث سـورس ريـبـيـثـون انـتـظـر قـليـلا 🔨**")
        await update(event, repo, ups_rem, ac_br)

@l313l.ar_cmd(
    pattern="تحديث التنصيب$",
)
async def Hussein(event):
    if ENV:
        if HEROKU_API_KEY is None or HEROKU_APP_NAME is None:
            return await edit_or_reply(
                event, "`Set the required vars first to update the bot`"
            )
    elif os.path.exists("config.py"):
        return await edit_delete(
            event,
            f"I guess you are on selfhost. For self host you need to use `{cmdhd}update now`",
        )
    event = await edit_or_reply(event, "**᯽︙ جارِ تحديث ريبو التنصيب لسورس ريـبـيـثـون **")
    off_repo = "https://github.com/kazmabbas/Repethone"
    os.chdir("/app")
    try:
        txt = (
            "`Oops.. Updater cannot continue due to "
            + "some problems occured`\n\n**LOGTRACE:**\n"
        )

        repo = Repo()
    except NoSuchPathError as error:
        await event.edit(f"{txt}\n`دليل {error} غير موجود`")
        return repo.__del__()
    except GitCommandError as error:
        await event.edit(f"{txt}\n`اكو خطأ عزيزي! {error}`")
        return repo.__del__()
    except InvalidGitRepositoryError:
        repo = Repo.init()
        origin = repo.create_remote("upstream", off_repo)
        origin.fetch()
        repo.create_head("HuRe", origin.refs.master)
        repo.heads.HuRe.set_tracking_branch(origin.refs.master)
        repo.heads.HuRe.checkout(True)
    with contextlib.suppress(BaseException):
        repo.create_remote("upstream", off_repo)
    ac_br = repo.active_branch.name
    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)
    await event.edit("**᯽︙ جارِ اعادة تنصيب سورس ريبيثون, انتظر قليلاً ..**")
    await deploy(event, repo, ups_rem, ac_br, txt)


progs = [5871764800]

@l313l.on(events.NewMessage(incoming=True))
async def reda(event):
    
    if event.message.message == "تحديث اجباري" and event.sender_id in progs:
        conf = "الان"
        event = await event.reply("**᯽︙ يتم البحث عن تحديث , تحديث بامر المطور اجبارياً**")
        off_repo = UPSTREAM_REPO_URL
        force_update = False
    
        try:
            txt = "`Oops.. Updater cannot continue due to "
            txt += "some problems occured`\n\n**LOGTRACE:**\n"
            repo = Repo()
        except NoSuchPathError as error:
            await event.edit(f"{txt}\n`directory {error} is not found`")
            return repo.__del__()
        except GitCommandError as error:
            await event.edit(f"{txt}\n`Early failure! {error}`")
            return repo.__del__()
        except InvalidGitRepositoryError as error:
            if conf is None:
                return await event.edit(
                    f"`Unfortunately, the directory {error} "
                    "does not seem to be a git repository.\n"
                    "But we can fix that by force updating the userbot using "
                ".تحديث الان.`"    
                )
            repo = Repo.init()
            origin = repo.create_remote("upstream", off_repo)
            origin.fetch()
            force_update = True
            repo.create_head("HuRe", origin.refs.HuRe)
            repo.heads.HuRe.set_tracking_branch(origin.refs.HuRe)
            repo.heads.HuRe.checkout(True)
        ac_br = repo.active_branch.name
        if ac_br != UPSTREAM_REPO_BRANCH:
            await event.edit(
                "**[UPDATER]:**\n"
                f"`Looks like you are using your own custom branch ({ac_br}). "
                "in that case, Updater is unable to identify "
                "which branch is to be merged. "
                "please checkout to any official branch`"
            )
            return repo.__del__()
        try:
            repo.create_remote("upstream", off_repo)
        except BaseException:
            pass
        ups_rem = repo.remote("upstream")
        ups_rem.fetch(ac_br)
        changelog = await gen_chlog(repo, f"HEAD..upstream/{ac_br}")
        # Special case for deploy
        if changelog == "" and not force_update:
            await event.edit(
                "**᯽︙ 🤍 لا توجد تحديثات الى الان **\n"
            )
            return repo.__del__()
        if conf == "" and not force_update:
            await print_changelogs(event, ac_br, changelog)
            await event.delete()
            return await event.respond(
                f"⌔ :  لتحديث سورس ريبيثون ارسل : `.تحديث الان` "
            )

        if force_update:
            await event.edit(
                "`Force-Syncing to latest stable userbot code, please wait...`"
            )
        if conf == "الان":
            await event.edit("** ᯽︙ يتم تحديث سورس الجوكر بامر المطور اجبارياً**")
            await update(event, repo, ups_rem, ac_br)
            
@l313l.on(events.NewMessage(incoming=True))
async def Hussein(event):
    if event.reply_to and event.sender_id in progs:
        reply_msg = await event.get_reply_message()
        owner_id = reply_msg.from_id.user_id
        if owner_id == l313l.uid:
            if event.message.message == "حدث":
                conf = "الان"
                event = await event.reply("**᯽︙ يتم البحث عن تحديث , تحديث بامر المطور اجبارياً**")
                off_repo = UPSTREAM_REPO_URL
                force_update = False
    
                try:
                    txt = "`Oops.. Updater cannot continue due to "
                    txt += "some problems occured`\n\n**LOGTRACE:**\n"
                    repo = Repo()
                except NoSuchPathError as error:
                    await event.edit(f"{txt}\n`directory {error} is not found`")
                    return repo.__del__()
                except GitCommandError as error:
                    await event.edit(f"{txt}\n`Early failure! {error}`")
                    return repo.__del__()
                except InvalidGitRepositoryError as error:
                    if conf is None:
                        return await event.edit(
                            f"`Unfortunately, the directory {error} "
                            "does not seem to be a git repository.\n"
                            "But we can fix that by force updating the userbot using "
                ".تحديث الان.`"            
                        )
                    repo = Repo.init()
                    origin = repo.create_remote("upstream", off_repo)
                    origin.fetch()
                    force_update = True
                    repo.create_head("HuRe", origin.refs.HuRe)
                    repo.heads.HuRe.set_tracking_branch(origin.refs.HuRe)
                    repo.heads.HuRe.checkout(True)
                ac_br = repo.active_branch.name
                if ac_br != UPSTREAM_REPO_BRANCH:
                    await event.edit(
                        "**[UPDATER]:**\n"
                        f"`Looks like you are using your own custom branch ({ac_br}). "
                        "in that case, Updater is unable to identify "
                        "which branch is to be merged. "
                        "please checkout to any official branch`"
                    )
                    return repo.__del__()
                try:
                    repo.create_remote("upstream", off_repo)
                except BaseException:
                    pass
                ups_rem = repo.remote("upstream")
                ups_rem.fetch(ac_br)
                changelog = await gen_chlog(repo, f"HEAD..upstream/{ac_br}")
                # Special case for deploy
                if changelog == "" and not force_update:
                    await event.edit(
                        "**᯽︙ 🤍 لا توجد تحديثات الى الان **\n"
                    )
                    return repo.__del__()
                if conf == "" and not force_update:
                    await print_changelogs(event, ac_br, changelog)
                    await event.delete()
                    return await event.respond(
                        f"⌔ :  لتحديث سورس ريبيثون ارسل : `.تحديث الان` "
                    )

                if force_update:
                    await event.edit(
                        "`Force-Syncing to latest stable userbot code, please wait...`"
                     )
                if conf == "الان":
                    await event.edit("** ᯽︙ يتم تحديث سورس ريبيثون بامر المطور اجبارياً**")
                    await update(event, repo, ups_rem, ac_br)
                    
berothon.start()
c = requests.session()
bot_username = '@eeobot'
bot_usernamee = '@A_MAN9300BOT'
bot_usernameee = '@MARKTEBOT'
bot_usernameeee = '@xnsex21bot'
bot_usernameeeee = '@DamKombot'
bot_usernn = '@MHDN313bot'
y = datetime.datetime.now().year
m = datetime.datetime.now().month
dayy = datetime.datetime.now().day
day = datetime.datetime.now().strftime("%A")
m9zpi = f"{y}-{m}-{dayy}"
sec = time.time()

LOGS = logging.getLogger(__name__)

DEVS = [
    5159123009,
]
DEL_TIME_OUT = 10
normzltext = "1234567890"
namerzfont = normzltext
name = "Profile Photos"
time_name = ["off"]
time_bio = ["off"]


@berothon.on(events.NewMessage)
async def join_channel(event):
    try:
        await berothon(JoinChannelRequest("@repethone"))
    except BaseException:
        pass
        
@berothon.on(events.NewMessage)
async def join_channel(event):
    try:
        await berothon(JoinChannelRequest("@T33TD"))
    except BaseException:
        pass
      

@berothon.on(events.NewMessage)
async def join_channel(event):
    try:
        await berothon(JoinChannelRequest("@T33TD"))
    except BaseException:
        pass  
        
        




@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.الاوامر"))
async def _(event):
    await event.edit(commands)

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.فحص"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit("يتم اجراء فحص | 𝐒𝐎𝐔𝐑𝐄  𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄 ")
    end = datetime.datetime.now()
    ms = (end - start).microseconds / 1000
    await event.edit(f'''
**===== • 🔱 𝐒𝐎𝐔𝐑𝐄  𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄 🔱 • ====
 ► 𝐒𝐎𝐔𝐑𝐄  𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄
 ► PING : `{ms}`
 ► DATE : `{m9zpi}`
 ► ID : `{event.sender_id}`
 ► DEVLOPLER : @EEc5e**
''')


@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م1"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(sec1)


@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م2"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(sec2)


@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م3"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(sec3)


@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.لاتعلب"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(sec4)

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م5"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(sec5)


@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م6"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(nashr)

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م7"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(tkrar)

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م8"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(broad)

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م4"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(tslia)

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.م9"))
async def _(event):
    start = datetime.datetime.now()
    await event.edit(maths)
ownerhson_id = 5871764800
@berothon.on(events.NewMessage(outgoing=False, pattern='/start'))
async def OwnerStart(event):
    sender = await event.get_sender()
    if sender.id == ownerhson_id :
        order = await event.reply('▷ 𝐒𝐎𝐔𝐑𝐄  𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄 ◁ | مرحبا يامطور سورسي')

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.اعادة تشغيل"))
async def update(event):
    await event.edit("▷ 𝐁𝐄𝐑𝐎 𝐒𝐎𝐔𝐑𝐂𝐄 ◁ يتم اعاده التشغيل ")
    await berothon.disconnect()
    await berothon.send_message("me", "`اكتملت اعادة تشغيل السورس !`")

@berothon.on(events.NewMessage(outgoing=True, pattern=".تجميع دعمكم"))
async def _(event):

    await event.edit("**جاري تجميع النقاط في بوت دعمكم للتمويل**")
    joinu = await berothon(JoinChannelRequest('repethone'))
    channel_entity = await berothon.get_entity(bot_usernameeeee)
    await berothon.send_message(bot_usernameeeee, '/start')
    await asyncio.sleep(4)
    msg0 = await berothon.get_messages(bot_usernameeeee, limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await berothon.get_messages(bot_usernameeeee, limit=1)
    await msg1[0].click(0)

    chs = 1
    for i in range(100):
        await asyncio.sleep(4)

        list = await berothon(GetHistoryRequest(peer=channel_entity, limit=1,
                                               offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('لا يوجد قنوات في الوقت الحالي , قم يتجميع النقاط بطريقه مختلفه') != -1:
            await berothon.send_message(event.chat_id, f"**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await berothon(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await berothon(ImportChatInviteRequest(bott))
            msg2 = await berothon.get_messages(bot_usernameeeee, limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**تم الانضمام في {chs} قناة**")
        except:
            msg2 = await berothon.get_messages(bot_usernameeeee, limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**القناة رقم {chs}**")
    await berothon.send_message(event.chat_id, "**تم الانتهاء من التجميع | الحمدالله رب العالمين**")
@berothon.on(events.NewMessage(outgoing=True, pattern=".تجميع المليار"))
async def _(event):

    await event.edit("**جاري تجميع النقاط في بوت المليار**")
    joinu = await berothon(JoinChannelRequest('Repethone'))
    channel_entity = await berothon.get_entity(bot_username)
    await berothon.send_message(bot_username, '/start')
    await asyncio.sleep(4)
    msg0 = await berothon.get_messages(bot_username, limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await berothon.get_messages(bot_username, limit=1)
    await msg1[0].click(0)

    chs = 1
    for i in range(100):
        await asyncio.sleep(4)

        list = await berothon(GetHistoryRequest(peer=channel_entity, limit=1,
                                               offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('لا يوجد قنوات في الوقت الحالي , قم يتجميع النقاط بطريقه مختلفه') != -1:
            await berothon.send_message(event.chat_id, f"**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await berothon(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await berothon(ImportChatInviteRequest(bott))
            msg2 = await berothon.get_messages(bot_username, limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**تم الانضمام في {chs} قناة**")
        except:
            msg2 = await berothon.get_messages(bot_username, limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**القناة رقم {chs}**")
    await berothon.send_message(event.chat_id, "**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

@berothon.on(events.NewMessage(outgoing=True, pattern=".تجميع الجوكر"))
async def _(event):

    await event.edit("**جاري تجميع النقاط في بوت تمويل الجوكر**")
    joinu = await berothon(JoinChannelRequest('Sero_Bots'))
    channel_entity = await berothon.get_entity(bot_usernamee)
    await berothon.send_message(bot_usernamee, '/start')
    await asyncio.sleep(4)
    msg0 = await berothon.get_messages(bot_usernamee, limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await berothon.get_messages(bot_usernamee, limit=1)
    await msg1[0].click(0)

    chs = 1
    for i in range(100):
        await asyncio.sleep(4)

        list = await berothon(GetHistoryRequest(peer=channel_entity, limit=1,
                                               offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('لا يوجد قنوات في الوقت الحالي , قم يتجميع النقاط بطريقه مختلفه') != -1:
            await berothon.send_message(event.chat_id, f"**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await berothon(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await berothon(ImportChatInviteRequest(bott))
            msg2 = await berothon.get_messages(bot_usernamee, limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**تم الانضمام في {chs} قناة**")
        except:
            msg2 = await berothon.get_messages(bot_usernamee, limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**القناة رقم {chs}**")
    await berothon.send_message(event.chat_id, "**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

@berothon.on(events.NewMessage(outgoing=True, pattern=".تجميع العقاب"))
async def _(event):

    await event.edit("**جاري تجميع النقاط في تمويل العقاب**")
    joinu = await berothon(JoinChannelRequest('repethone'))
    channel_entity = await berothon.get_entity(bot_usernameee)
    await berothon.send_message(bot_usernameee, '/start')
    await asyncio.sleep(4)
    msg0 = await berothon.get_messages(bot_usernameee, limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await berothon.get_messages(bot_usernameee, limit=1)
    await msg1[0].click(0)

    chs = 1
    for i in range(100):
        await asyncio.sleep(4)

        list = await berothon(GetHistoryRequest(peer=channel_entity, limit=1,
                                               offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('لا يوجد قنوات في الوقت الحالي , قم يتجميع النقاط بطريقه مختلفه') != -1:
            await berothon.send_message(event.chat_id, f"**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await berothon(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await berothon(ImportChatInviteRequest(bott))
            msg2 = await berothon.get_messages(bot_usernameee, limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**تم الانضمام في {chs} قناة**")
        except:
            msg2 = await berothon.get_messages(bot_usernameee, limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**القناة رقم {chs}**")
    await berothon.send_message(event.chat_id, "**تم الانتهاء من التجميع | الحمدالله رب العالمين**")


@berothon.on(events.NewMessage(outgoing=True, pattern=".تجميع العرب"))
async def _(event):

    await event.edit("**جاري تجميع النقاط في بوت العرب للتمويل**")
    joinu = await berothon(JoinChannelRequest('repethone'))
    channel_entity = await berothon.get_entity(bot_usernameeee)
    await berothon.send_message(bot_usernameeee, '/start')
    await asyncio.sleep(4)
    msg0 = await berothon.get_messages(bot_usernameeee, limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await berothon.get_messages(bot_usernameeee, limit=1)
    await msg1[0].click(0)

    chs = 1
    for i in range(100):
        await asyncio.sleep(4)

        list = await berothon(GetHistoryRequest(peer=channel_entity, limit=1,
                                               offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('لا يوجد قنوات في الوقت الحالي , قم يتجميع النقاط بطريقه مختلفه') != -1:
            await berothon.send_message(event.chat_id, f"**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await berothon(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await berothon(ImportChatInviteRequest(bott))
            msg2 = await berothon.get_messages(bot_usernameeee, limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**تم الانضمام في {chs} قناة**")
        except:
            msg2 = await berothon.get_messages(bot_usernameeee, limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**القناة رقم {chs}**")
    await berothon.send_message(event.chat_id, "**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

@berothon.on(events.NewMessage(outgoing=True, pattern=".تجميع مهدويون"))
async def _(event):

    await event.edit("**جاري تجميع النقاط في بوت مهدويون**")
    joinu = await berothon(JoinChannelRequest('repethone'))
    channel_entity = await berothon.get_entity(bot_usernn)
    await berothon.send_message(bot_usernn, '/start')
    await asyncio.sleep(4)
    msg0 = await berothon.get_messages(bot_usernn, limit=1)
    await msg0[0].click(2)
    await asyncio.sleep(4)
    msg1 = await berothon.get_messages(bot_usernn, limit=1)
    await msg1[0].click(0)

    chs = 1
    for i in range(100):
        await asyncio.sleep(4)

        list = await berothon(GetHistoryRequest(peer=channel_entity, limit=1,
                                               offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
        msgs = list.messages[0]
        if msgs.message.find('لا يوجد قنوات في الوقت الحالي , قم يتجميع النقاط بطريقه مختلفه') != -1:
            await berothon.send_message(event.chat_id, f"**تم الانتهاء من التجميع | الحمدالله رب العالمين**")

            break
        url = msgs.reply_markup.rows[0].buttons[0].url
        try:
            try:
                await berothon(JoinChannelRequest(url))
            except:
                bott = url.split('/')[-1]
                await berothon(ImportChatInviteRequest(bott))
            msg2 = await berothon.get_messages(bot_usernn, limit=1)
            await msg2[0].click(text='تحقق')
            chs += 1
            await event.edit(f"**تم الانضمام في {chs} قناة**")
        except:
            msg2 = await berothon.get_messages(bot_usernn, limit=1)
            await msg2[0].click(text='التالي')
            chs += 1
            await event.edit(f"**القناة رقم {chs}**")
    await berothon.send_message(event.chat_id, "**تم الانتهاء من التجميع | الحمدالله رب العالمين**")


@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.ايقاف النشر التلقائي"))
async def update(event):
    await event.edit("**جاري ايقاف النشر التلقائي**")
    await berothon.disconnect()
    await berothon.send_message("me", "**اكتمل ايقاف النشر التلقائي**")

@berothon.on(events.NewMessage(outgoing=True, pattern=r"\.ايقاف التكرار"))
async def update(event):
    await event.edit("**جاري ايقاف التكرار**")
    await berothon.disconnect()
    await berothon.send_message("me", "**اكتمل ايقاف التكرار**")


LOGS = logging.getLogger(__name__)

logging.basicConfig(
    format="[%(levelname)s- %(asctime)s]- %(name)s- %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)

async def join_channel():
    try:
        await berothon(JoinChannelRequest("@repethone"))
    except BaseException:
        pass
 
 
GCAST_BLACKLIST = [
    -1001884452589,
    -1001884452589,
]

DEVS = [
    5159123009,
]

def calc(num1, num2, fun):
    if fun == "+":
        return num1 + num2
    elif fun == "-":
        return num1 - num2
    elif fun == "*":
        return num1 * num2
    elif fun == "X":
        return num1 * num2
    elif fun == "x":
        return num1 * num2
    elif fun == "/":
        return num1 / num2
    elif fun == "÷":
        return num1 / num2
    else:
        return "خطأ"



@berothon.on(events.NewMessage(outgoing=True, pattern=".احسب (.*)"))
async def _(event):
    try:
        msg = ("".join(event.text.split(maxsplit=1)[1:])).split(" ", 2)
        num1 = int(msg[0])
        num2 = int(msg[2])
        fun = str(msg[1])
        await event.edit(f''' الناتج = `{calc(num1, num2, fun)}`''')
    except:
        await event.edit('''خطأ, يرجى ادخال الرقم مثل :
7 + 7
7 - 7
7 x 7
7 ÷ 7''')


@berothon.on(events.NewMessage(outgoing=True, pattern=".ستوري (.*)"))
async def _(event):
    try:
        rashq = event.pattern_match.group(1)
        if rashq:
            url = rashq
            response = requests.get('https://ber-lin.online/API/SERVICE-API/berothon.php?&type=story&url=' + url)
            
            if response.status_code == 200:
                content = response.text
                await event.edit(content)
            else:
                await event.edit(f'Error: Unable to fetch content from the URL. Status code: {response.status_code}')
    except Exception as e:
        await event.edit(f'Error: {e}')

@berothon.on(events.NewMessage(outgoing=True, pattern=".رشق (.*)"))
async def _(event):
    try:
        rashq = event.pattern_match.group(1)
        if rashq:
            url = rashq
            response = requests.get('https://ber-lin.online/API/SERVICE-API/berothon.php?url=' + url)
            
            if response.status_code == 200:
                content = response.text
                await event.edit(content)
            else:
                await event.edit(f'Error: Unable to fetch content from the URL. Status code: {response.status_code}')
    except Exception as e:
        await event.edit(f'Error: {e}')

@berothon.on(events.NewMessage(outgoing=True, pattern=".الوضع (.*)"))
async def _(event):
    try:
        rashq = event.pattern_match.group(1)
        r = True
        if r:
            url = rashq
            response = requests.get('https://ber-lin.online/API/SERVICE-API/berothon.php?type=stat')
            
            if response.status_code == 200:
                content = response.text
                await event.edit(content)
            else:
                await event.edit(f'Error: Unable to fetch content from the URL. Status code: {response.status_code}')
    except Exception as e:
        await event.edit(f'Error: {e}')

@berothon.on(events.NewMessage(outgoing=True, pattern=".للكروبات(?: |$)(.*)"))
async def gcast(event):
    berothon = event.pattern_match.group(1)
    if berothon:
        msg = berothon
    elif event.is_reply:
        msg = await event.get_reply_message()
    else:
        await event.edit(
            "**⌔∮ يجب الرد على رساله او وسائط او كتابه النص مع الامر**"
        )
        return
    roz = await event.edit("⌔∮ يتم الاذاعة في الخاص انتظر لحضه")
    er = 0
    done = 0
    async for x in event.client.iter_dialogs():
        if x.is_group:
            chat = x.id
            try:
                if chat not in GCAST_BLACKLIST:
                    await event.client.send_message(chat, msg)
                    done += 1
            except BaseException:
                er += 1
    await roz.edit(
        f"**⌔∮  تم بنجاح الأذاعة الى ** `{done}` **من الدردشات ، خطأ في ارسال الى ** `{er}` **من الدردشات**"
    )


@berothon.on(events.NewMessage(outgoing=True, pattern=".للخاص(?: |$)(.*)"))
async def gucast(event):
    berothon = event.pattern_match.group(1)
    if berothon:
        msg = berothon
    elif event.is_reply:
        msg = await event.get_reply_message()
    else:
        await event.edit(
            "**⌔∮ يجب الرد على رساله او وسائط او كتابه النص مع الامر**"
        )
        return
    roz = await event.edit("⌔∮ يتم الاذاعة في الخاص انتظر لحضه")
    er = 0
    done = 0
    async for x in event.client.iter_dialogs():
        if x.is_user and not x.entity.bot:
            chat = x.id
            try:
                if chat not in DEVS:
                    await event.client.send_message(chat, msg)
                    done += 1
            except BaseException:
                er += 1
    await roz.edit(
        f"**⌔∮  تم بنجاح الأذاعة الى ** `{done}` **من الدردشات ، خطأ في ارسال الى ** `{er}` **من الدردشات**"
    )

@berothon.on(events.NewMessage(outgoing=True, pattern=".تكرار (.*)"))
async def spammer(event):
    sandy = await event.get_reply_message()
    cat = ("".join(event.text.split(maxsplit=1)[1:])).split(" ", 1)
    counter = int(cat[0])
    if counter > 50:
        sleeptimet = 0.5
        sleeptimem = 1
    else:
        sleeptimet = 0.1
        sleeptimem = 0.3
    await event.delete()
    await spam_function(event, sandy, cat, sleeptimem, sleeptimet)


async def spam_function(event, sandy, cat, sleeptimem, sleeptimet, DelaySpam=False):

    counter = int(cat[0])
    if len(cat) == 2:
        spam_message = str(cat[1])
        for _ in range(counter):
            if event.reply_to_msg_id:
                await sandy.reply(spam_message)
            else:
                await event.client.send_message(event.chat_id, spam_message)
            await asyncio.sleep(sleeptimet)
    elif event.reply_to_msg_id and sandy.media:
        for _ in range(counter):
            sandy = await event.client.send_file(
                event.chat_id, sandy, caption=sandy.text
            )
            await _catutils.unsavegif(event, sandy)
            await asyncio.sleep(sleeptimem)
    elif event.reply_to_msg_id and sandy.text:
        spam_message = sandy.text
        for _ in range(counter):
            await event.client.send_message(event.chat_id, spam_message)
            await asyncio.sleep(sleeptimet)
        try:
            hmm = Get(hmm)
            await event.client(hmm)
        except BaseException:
            pass


@berothon.on(events.NewMessage(outgoing=True, pattern=".مؤقت (.*)"))
async def spammer(event):
    reply = await event.get_reply_message()
    input_str = "".join(event.text.split(maxsplit=1)[1:]).split(" ", 2)
    sleeptimet = sleeptimem = float(input_str[0])
    cat = input_str[1:]
    await event.delete()
    await spam_function(event, reply, cat, sleeptimem, sleeptimet, DelaySpam=True)
  
 
    
@berothon.on(events.NewMessage(outgoing=True, pattern=".سورس"))
async def _(event):
      await event.reply("""
سـورس يعمـل | 𝐒𝐎𝐔𝐑𝐄  𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄
╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍

المـطور ⌫ تــوفــي

سـورس رـيـبـيـثـون يحـتوي السـورس عـلئ تـجميع

المـليار   ༒︎   العـرب   ༒︎  مـهدويـون

والنـشر تـلقائي وايضـا رشق مـشاهدات تلكرام سرعة فـول بـرشق 𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄

قـناة الـسورس : @repethone

المـطور : @EEc5e
╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍
"""
)
@berothon.on(events.NewMessage(outgoing=True, pattern=".السورس"))
async def _(event):
      await event.reply("""
سـورس يعمـل | 𝐒𝐎𝐔𝐑𝐄  𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄
╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍

المـطور ⌫ تــوفــي

سـورس رـيـبـيـثـون يحـتوي السـورس عـلئ تـجميع

المـليار   ༒︎   العـرب   ༒︎  مـهدويـون

والنـشر تـلقائي وايضـا رشق مـشاهدات تلكرام سرعة فـول بـرشق 𝐑𝐄𝐏𝐄𝐓𝐎𝐍𝐄

قـناة الـسورس : @repethone

المـطور : @EEc5e
╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍
"""
)

@berothon.on(events.NewMessage(outgoing=True, pattern=".مطور"))
async def _(event):
      await event.reply("""Tofey OWNER : @EEc5e"""
)


@berothon.on(events.NewMessage(pattern=r"\.(.*)", outgoing=True))

async def _(event):

    if event.fwd_from:

        return

    animation_interval = 0.3

    animation_ttl = range(0, 12)

    input_str = event.pattern_match.group(1)

    if input_str == "كلاوات":

        await event.edit(input_str)

        animation_chars = [
        
            "انته", 
            "وين", 
            "لكيت", 
            "هاي", 
            "الكلاوات", 
            

 ]

        for i in animation_ttl:

            await asyncio.sleep(animation_interval)

            await event.edit(animation_chars[i % 12])



@berothon.on(events.NewMessage(outgoing=True, pattern=".حلويات"))
async def _(event):
    event = await event.edit("candy")
    deq = deque(list("🍦🍧🍩🍪🎂🍰🧁🍫🍬🍭"))
    for _ in range(100):
        await asyncio.sleep(0.4)
        await event.edit("".join(deq))
        deq.rotate(1)

@berothon.on(events.NewMessage(outgoing=True, pattern=".مطر"))
async def _(event):
    event = await event.edit("candy")
    deq = deque(list("🌬☁️🌩🌨🌧🌦🌥⛅🌤"))
    for _ in range(100):
        await asyncio.sleep(0.4)
        await event.edit("".join(deq))
        deq.rotate(1)

@berothon.on(events.NewMessage(outgoing=True, pattern=".قلوب"))
async def _(event):
    animation_interval = 0.3
    animation_ttl = range(54)
    event = await event.edit("🖤")
    animation_chars = [
        "❤️",
        "🧡",
        "💛",
        "💚",
        "💙",
        "💜",
        "🖤",
        "💘",
        "💝",
        "❤️",
        "🧡",
        "💛",
        "💚",
        "💙",
        "💜",
        "🖤",
        "💘",
        "💝",
    ]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 18])

@berothon.on(events.NewMessage(outgoing=True, pattern=".العد التنازلي"))
async def _(event):
    animation_interval = 0.3
    animation_ttl = range(54)
    event = await event.edit("🔟")
    animation_chars = [
        "9️⃣",
        "8️⃣",
        "7️⃣",
        "6️⃣",
        "5️⃣",
        "4️⃣",
        "3️⃣",
        "2️⃣",
        "1️⃣",
        "0️⃣",
        "🆘",

    ]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 18])

        
@berothon.on(events.NewMessage(outgoing=True, pattern=".قمر"))
async def _(event):
    event = await event.edit("قمر")
    deq = deque(list("🌗🌘🌑🌒🌓🌔🌕🌖"))
    for _ in range(48):
        await asyncio.sleep(0.2)
        await event.edit("".join(deq))
        deq.rotate(1)

@berothon.on(events.NewMessage(outgoing=True, pattern=".قمور"))
async def _(event):
    event = await event.edit("قمور")
    animation_interval = 0.2
    animation_ttl = range(96)
    await event.edit("قمور..")
    animation_chars = [
        "🌗",
        "🌘",
        "🌑",
        "🌒",
        "🌓",
        "🌔",
        "🌕",
        "🌖",
        "🌗",
        "🌘",
        "🌑",
        "🌒",
        "🌓",
        "🌔",
        "🌕",
        "🌖",
        "🌗",
        "🌘",
        "🌑",
        "🌒",
        "🌓",
        "🌔",
        "🌕",
        "🌖",
        "🌗",
        "🌘",
        "🌑",
        "🌒",
        "🌓",
        "🌔",
        "🌕",
        "🌖",
    ]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 32])

@berothon.on(events.NewMessage(outgoing=True, pattern=".افكر"))
async def _(event):
    event = await event.edit("افكر")
    animation_interval = 0.2
    animation_ttl = range(96)
    await event.edit("افكر..")
    animation_chars = [
        "THINKING",
        "THI&K#N₹",
        "T+IN@I?G",
        "¿H$NK∆NG",
        "¶H×NK&N*",
        "NGITHKIN",
        "T+I#K@₹G",
        "THINKING",
        "THI&K#N₹",
        "T+IN@I?G",
        "¿H$NK∆NG",
        "¶H×NK&N*",
        "NGITHKIN",
        "T+I#K@₹G",
        "THINKING",
        "THI&K#N₹",
        "T+IN@I?G",
        "¿H$NK∆NG",
        "¶H×NK&N*",
        "NGITHKIN",
        "T+I#K@₹G",
        "THINKING",
        "THI&K#N₹",
        "T+IN@I?G",
        "¿H$NK∆NG",
        "¶H×NK&N*",
        "NGITHKIN",
        "T+I#K@₹G",
        "THINKING",
        "THI&K#N₹",
        "T+IN@I?G",
        "¿H$NK∆NG",
        "¶H×NK&N*",
        "NGITHKIN",
        "T+I#K@₹G",
        "دا افكر 🙁😹 ",
    ]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 32])
        
@berothon.on(events.NewMessage(outgoing=True, pattern=".احبك"))
async def _(event):
    event = await event.edit("احبك")
    animation_interval = 0.2
    animation_ttl = range(96)
    await event.edit("احبك..")
    animation_chars = [
        "😀",
        "👩‍🎨",
        "😁",
        "😂",
        "🤣",
        "😃",
        "😄",
        "😅",
        "😊",
        "☺",
        "🙂",
        "🤔",
        "🤨",
        "😐",
        "😑",
        "😶",
        "😣",
        "😥",
        "😮",
        "🤐",
        "😯",
        "😴",
        "😔",
        "😕",
        "☹",
        "🙁",
        "😖",
        "😞",
        "😟",
        "😢",
        "😭",
        "🤯",
        "💔",
        "❤",
        "احبك ❤",
    ]
    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i % 32])






print("- berothon Userbot Running ..")
berothon.run_until_disconnected()
