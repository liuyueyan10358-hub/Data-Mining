from pathlib import Path
from xml.sax.saxutils import escape
import json, re
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path('/Users/yueyan_liu/Desktop/Data Mining/project')
OUT = ROOT / 'output/pdf'
TMP = ROOT / 'tmp/pdfs'
OUT.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('CN', '/System/Library/Fonts/STHeiti Light.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('CNB', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Mono', '/System/Library/Fonts/Menlo.ttc', subfontIndex=0))
pdfmetrics.registerFontFamily('CN', normal='CN', bold='CNB', italic='CN', boldItalic='CNB')
W, H = A4
M = 48
CW = W-2*M
NAVY = '#142A3B'
TEAL = '#087F8C'
ORANGE = '#E87835'
INK = '#233746'
MUTED = '#657887'
LIGHT = '#EDF5F6'
SOURCES = {}

def src(key, title, url):
    SOURCES[key] = (title, url)

def rich(s):
    s = escape(s)
    s = re.sub(r'`([^`]+)`', r'<font name="Mono" size="9">\1</font>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    return s.replace('\n', '<br/>')

def para(s, size=10.5, leading=17.7, color=INK, bold=False, raw=False):
    st = ParagraphStyle('p',fontName='CNB' if bold else 'CN',fontSize=size,leading=leading,
                        textColor=colors.HexColor(color), wordWrap='CJK',
                        allowWidows=0, allowOrphans=0)
    return Paragraph(s if raw else rich(s), st)

class Book:
    def __init__(self, filename, title, tag, pages):
        self.path = OUT/filename
        self.c = canvas.Canvas(str(self.path), pagesize=A4, pageCompression=1)
        self.c.setTitle(title)
        self.c.setAuthor('Codex')
        self.c.setSubject('中文 GitHub 学习教程与 Git / GitHub 命令参考；2026-10-31')
        self.title, self.tag, self.pages = title, tag, pages
        self.index = 0
        self.bottoms = []
    def check(self, amount):
        if self.y-amount < 61:
            raise ValueError(f'{self.path.name} page {self.index}: overflow y={self.y:.1f}, need={amount:.1f}')
    def put(self, ob, gap=8):
        ww, hh = ob.wrap(CW, 2000)
        self.check(hh+gap)
        ob.drawOn(self.c, M, self.y-hh)
        self.y -= hh+gap
    def p(self,s): self.put(para(s))
    def h(self,s): self.put(para(s,12.5,19,TEAL,True),gap=7)
    def small(self,s): self.put(para(s,9,14,MUTED),gap=8)
    def code(self,s):
        lines=s.strip('\n').split('\n')
        fs=9.25
        maxw=max(pdfmetrics.stringWidth(line,'Mono',fs) for line in lines)
        if maxw>CW-28: fs*= (CW-28)/maxw
        if fs<7.6: raise ValueError(f'Code line too wide, page {self.index}: {s}')
        lh=14.4
        hh=len(lines)*lh+20
        self.check(hh+11)
        c=self.c
        c.setFillColor(colors.HexColor(NAVY))
        c.roundRect(M,self.y-hh,CW,hh,5,stroke=0,fill=1)
        c.setFont('Mono',fs)
        for i,line in enumerate(lines):
            c.setFillColor(colors.HexColor('#92B4C4' if line.lstrip().startswith('#') else '#F1F7F8'))
            c.drawString(M+14,self.y-16-i*lh,line)
        self.y-=hh+11
    def box(self,title,s,warn=False):
        fill='#FFF3E9' if warn else LIGHT
        accent=ORANGE if warn else TEAL
        titlep=para(title,10.5,16,accent,True)
        body=para(s,10,16.5)
        _,a=titlep.wrap(CW-30,1000); _,b=body.wrap(CW-30,1000)
        hh=a+b+27
        self.check(hh+11)
        c=self.c;c.setFillColor(colors.HexColor(fill))
        c.roundRect(M,self.y-hh,CW,hh,5,fill=1,stroke=0)
        c.setFillColor(colors.HexColor(accent));c.rect(M,self.y-hh,3,hh,stroke=0,fill=1)
        titlep.drawOn(c,M+15,self.y-12-a)
        body.drawOn(c,M+15,self.y-17-a-b)
        self.y-=hh+11
    def table(self,headers,rows,widths=None,code_first=False):
        widths=widths or [CW*0.32,CW*0.68]
        data=[[para(x,9.6,14,'#FFFFFF',True) for x in headers]]
        for row in rows:
            cells=[]
            for j,v in enumerate(row):
                if code_first and j==0:
                    cells.append(para('<font name="Mono" size="8.7">'+escape(v).replace('\n','<br/>')+'</font>',9,14,raw=True))
                else: cells.append(para(v,9.8,15.2))
            data.append(cells)
        t=Table(data,colWidths=widths,hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor(TEAL)),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F5F7'),colors.white]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
            ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
            ('LINEBELOW',(0,0),(-1,0),0.5,colors.HexColor(TEAL)),
        ]))
        self.put(t,11)
    def refs(self,*keys):
        parts=[]
        for k in keys:
            title,url=SOURCES[k]
            parts.append(f'<link href="{escape(url)}" color="{TEAL}">[{k}] {escape(title)}</link>')
        self.put(para('官方参考：'+'　 /　 '.join(parts),8,12.7,MUTED,raw=True),5)
    def flow(self,labels):
        c=self.c;hh=70;self.check(hh+12)
        bw=(CW-20*(len(labels)-1))/len(labels)
        for i,(top,bottom) in enumerate(labels):
            x=M+i*(bw+20)
            c.setFillColor(colors.HexColor(LIGHT));c.roundRect(x,self.y-60,bw,60,5,fill=1,stroke=0)
            c.setFillColor(colors.HexColor(TEAL));c.setFont('CNB',12);c.drawCentredString(x+bw/2,self.y-23,top)
            c.setFillColor(colors.HexColor(MUTED));c.setFont('CN',8.8);c.drawCentredString(x+bw/2,self.y-43,bottom)
            if i<len(labels)-1:
                c.setStrokeColor(colors.HexColor(TEAL));c.line(x+bw+4,self.y-30,x+bw+16,self.y-30)
                c.line(x+bw+12,self.y-26,x+bw+16,self.y-30);c.line(x+bw+12,self.y-34,x+bw+16,self.y-30)
        self.y-=hh+12
    def start(self,title,subtitle='',eyebrow=None):
        self.index+=1
        self.c.bookmarkPage(f'p{self.index}')
        self.c.addOutlineEntry(title,f'p{self.index}',0,False)
        self.y=H-49
        self.c.setFillColor(colors.HexColor(TEAL));self.c.setFont('CNB',8.5)
        self.c.drawString(M,self.y,eyebrow or f'{self.tag}  /  {self.index:02d}')
        self.y-=29
        self.put(para(title,23,30,NAVY,True),7)
        if subtitle: self.put(para(subtitle,10,16,MUTED),17)
        else: self.y-=7
    def end(self):
        self.bottoms.append(round(self.y,1))
        c=self.c;c.setStrokeColor(colors.HexColor('#CEDCE1'));c.setLineWidth(.5)
        c.line(M,44,W-M,44)
        c.setFont('CN',8);c.setFillColor(colors.HexColor(MUTED))
        c.drawString(M,29,self.title)
        c.drawRightString(W-M,29,f'{self.index:02d} / {self.pages:02d}')
        if self.index>2:
            c.linkRect('', 'p2' if self.tag=='LEARN' else 'p1', (M,23,M+180,39), relative=0, thickness=0)
        c.showPage()
    def cover(self,kind,headline,subtitle,items):
        self.index+=1;c=self.c;c.bookmarkPage('p1');c.addOutlineEntry(headline,'p1',0,False)
        c.setFillColor(colors.HexColor(NAVY));c.rect(0,0,W,H,fill=1,stroke=0)
        c.setFillColor(colors.HexColor('#4ED0CE'));c.setFont('Mono',11);c.drawString(M,H-64,'GITHUB  /  '+kind)
        c.setFillColor(colors.white);c.setFont('CNB',34)
        for i,line in enumerate(headline.split('\n')): c.drawString(M,H-147-i*50,line)
        self.y=H-290
        self.put(para(subtitle,13,22,'#C2D8E2'),20)
        self.y-=18
        for n,t,desc in items:
            c.setFillColor(colors.HexColor('#4ED0CE'));c.setFont('Mono',13);c.drawString(M,self.y,n)
            self.put(para(t,14,21,'#FFFFFF',True),6)
            self.put(para(desc,10.5,18,'#B8CDD6'),18)
        c.setStrokeColor(colors.HexColor('#4D6575'));c.line(M,92,W-M,92)
        c.setFillColor(colors.HexColor('#B8CDD6'));c.setFont('CN',9)
        c.drawString(M,70,'中文实用版  |  Windows · macOS · Linux')
        c.drawString(M,51,'编写与核对日期：2026-10-31  |  示例以 main 为主分支')
        self.bottoms.append(92);c.showPage()
    def toc(self,entries):
        for num,title,desc in entries:
            left=para(f'<link href="#p{num}" color="{INK}">{escape(title)}</link>',10.3,17,raw=True)
            _,hh=left.wrap(CW-35,1000);self.check(hh+6)
            left.drawOn(self.c,M,self.y-hh)
            self.c.setFillColor(colors.HexColor(TEAL));self.c.setFont('Mono',9)
            self.c.drawRightString(W-M,self.y-12,f'{num:02d}')
            self.c.linkRect('',f'p{num}',(M,self.y-hh-3,W-M,self.y+2),thickness=0)
            self.y-=hh+4
    def sources(self,keys):
        for k in keys:
            title,url=SOURCES[k]
            self.put(para(f'<font color="{TEAL}">[{k}]</font> <link href="{escape(url)}" color="{INK}">{escape(title)}</link>',10,16,raw=True),2)
            domain=url.split('/')[2]
            self.put(para(domain+'  |  点击标题打开官方原文',8.5,12,MUTED),4)
    def save(self):
        assert self.index==self.pages,(self.path,self.index,self.pages)
        self.c.save()
        return {'path':str(self.path),'pages':self.pages,'content_bottoms':self.bottoms}

src('01','GitHub Hello World','https://docs.github.com/en/get-started/using-github/hello-world')
src('02','安装与配置 Git','https://docs.github.com/en/get-started/git-basics/set-up-git')
src('03','远程仓库与 URL','https://docs.github.com/en/get-started/git-basics/about-remote-repositories')
src('04','HTTPS 与个人访问令牌','https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens')
src('05','生成 SSH 密钥与配置代理','https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent')
src('06','测试 SSH 连接','https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection')
src('07','GitHub 主机指纹','https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints')
src('08','下载、克隆与 Fork','https://docs.github.com/en/repositories/working-with-files/using-files/downloading-files-from-github')
src('09','Pull Request 快速入门','https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart')
src('10','命令行解决合并冲突','https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/resolving-a-merge-conflict-using-the-command-line')
src('11','同步 Fork','https://docs.github.com/en/pull-requests/how-tos/work-with-forks/syncing-a-fork')
src('12','GitHub 大文件限制','https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github')
src('13','清理泄露的敏感数据','https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository')
src('14','GitHub Actions 快速入门','https://docs.github.com/en/actions/get-started/quickstart')
src('15','创建 GitHub Pages 站点','https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site')
src('16','创建 Issue','https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue')
src('17','仓库许可证','https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository')
for key,cmd in [('18','restore'),('19','reset'),('20','revert'),('21','stash'),('22','reflog'),('23','pull'),('24','push'),('25','switch'),('26','merge'),('27','clean'),('28','config'),('29','ignore')]:
    src(key,'Git '+('gitignore' if cmd=='ignore' else cmd)+' 参考','https://git-scm.com/docs/'+('gitignore' if cmd=='ignore' else 'git-'+cmd))
for key,cmd in [('30','gh_auth_login'),('31','gh_repo_create'),('32','gh_pr_create'),('33','gh_pr_merge')]:
    src(key,cmd.replace('_',' ')+' 参考','https://cli.github.com/manual/'+cmd)
for key,cmd in [('34','add'),('35','commit'),('36','diff'),('37','log'),('38','tag'),('39','cherry-pick'),('40','rebase')]:
    src(key,'Git '+cmd+' 参考','https://git-scm.com/docs/git-'+cmd)
src('41','Git LFS 官方说明','https://git-lfs.com/')
src('42','管理 GitHub Release','https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository')

def build_tutorial():
    b=Book('GitHub_从零到协作完整教程.pdf','GitHub 从零到协作完整教程','LEARN',29)
    b.cover('LEARN','GitHub\n从零到协作','把项目保存好，把修改讲清楚，把团队工作连起来。\n零基础也能跟着完成一个真实工作流程。',[
        ('01','先建立直觉','区分 Git 和 GitHub，看懂版本、分支与远程仓库。'),
        ('02','再完成一次实践','网页入门、本地提交、推送和 Pull Request 全流程。'),
        ('03','最后学会应对变化','同步、冲突、撤销、找回修改与团队协作。')])
    b.start('阅读路线与目录','可点击目录跳转；左侧 PDF 书签也可导航。页脚标题可返回目录。')
    entries=[
        (3,'01 先分清：Git 与 GitHub',''),(4,'02 认识界面，准备账号与工具',''),
        (5,'03 安装 Git，设置提交身份',''),(6,'04 连接方式 A：HTTPS 登录',''),(7,'05 连接方式 B：SSH 密钥',''),
        (8,'06 不用命令行，先做一次网页练习',''),(9,'07 路线 A：克隆已有仓库',''),(10,'08 路线 B：上传电脑里的项目',''),
        (11,'09 保存一个版本：add 与 commit',''),(12,'10 整理仓库：忽略规则与 README',''),(13,'11 每天怎么同步与推送',''),
        (14,'12 用分支隔离一次修改',''),(15,'13 提交与合并 Pull Request',''),(16,'14 处理合并冲突',''),(17,'15 Fork：参与别人的项目',''),
        (18,'16 撤销：先判断修改在哪里',''),(19,'17 临时收纳与找回提交',''),(20,'18 Issue、Review 与团队规则',''),
        (21,'19 Tag、Release 与 Pages',''),(22,'20 Actions：自动运行检查',''),(23,'21 数据项目、大文件与秘密',''),
        (24,'22 排错：登录、权限与网络',''),(25,'23 排错：提交、分支与历史',''),(26,'24 综合练习与验收清单',''),
        (27,'25 术语对照与学习建议',''),(28,'官方参考资料 A',''),(29,'官方参考资料 B','')]
    b.toc(entries)
    b.small('首次学习：3-16 页 → 18-19 页 → 26 页。已有经验：直接按目录与配套指令手册查阅。')
    b.end()

    b.start('先分清：Git 与 GitHub','把 Git 想成电脑里的“版本记录员”，把 GitHub 想成网上的“项目协作室”。')
    b.table(['概念','通俗解释'],[
        ('Git','安装在电脑上的版本管理工具。可以离线记录修改、查看历史、建立分支。'),
        ('GitHub','托管 Git 仓库的网站，提供协作、PR、Issue、自动检查等功能。'),
        ('Repository / Repo','仓库。项目文件与它们的版本历史；本地通常有一个隐藏的 .git 文件夹。'),
        ('Commit','一次有说明的版本记录，有唯一标识（提交哈希）。它首先保存在本地。'),
        ('Branch / 分支','指向一系列提交的可移动名称。可以并行修改，再决定是否合并。')])
    b.h('一份修改，会经过四个位置')
    b.flow([('工作区','正在编辑的文件'),('暂存区','这次准备提交'),('本地历史','commit 后保存'),('GitHub','push 后共享')])
    b.p('`git add` 挑选内容，`git commit` 留下记录，`git push` 上传提交。`git fetch` 获取远程更新；`git pull` 还会把指定远程分支整合到当前分支。')
    b.box('三个容易混淆的点','保存文件 ≠ 提交；提交 ≠ 上传；删除电脑中的文件，也可能成为下次提交的一部分。Git 并不会自动记录每一次键盘输入。')
    b.refs('02','03');b.end()

    b.start('认识界面，准备账号与工具','不必一开始理解所有标签页。先知道自己应该去哪里。')
    b.table(['入口','用来做什么'],[
        ('Code','查看文件、分支、提交历史；复制克隆地址；下载 ZIP。'),
        ('Issues','记录问题、需求、任务与讨论。'),('Pull requests','提出修改、审阅修改、合并分支。'),
        ('Actions','查看自动测试、构建和部署结果。'),('Settings','权限、协作者、分支规则、Pages 等设置；需要相应权限。'),
        ('Releases / Tags','查看已发布版本、说明与下载附件。')])
    b.h('开始前准备这四样')
    b.p('1. 注册 GitHub 账号并验证邮箱。为账号设置双重验证，妥善保存恢复码。\n2. 安装 Git；准备终端和文本编辑器。Windows 示例建议统一使用 Git Bash。\n3. 新建一个专门的练习目录，不要在个人主目录或真实重要项目里试验撤销。\n4. 选择一种登录方式：第 6 页 HTTPS，或第 7 页 SSH。')
    b.box('可以先走图形界面','网页适合阅读与小修改；GitHub Desktop 适合图形化提交、分支和同步；终端适合稳定复用指令。工具不同，仓库与提交的概念相同。')
    b.refs('01','02');b.end()

    b.start('安装 Git，设置提交身份','本教程使用较新版本 Git 的 switch、restore 和 init -b；遇到未知选项时先升级 Git。')
    b.table(['系统','安装与打开终端'],[
        ('Windows','从 git-scm.com 官方安装入口安装 Git for Windows。打开 Git Bash 后跟着本教程操作。'),
        ('macOS','终端执行 git --version 检查；未安装时可按系统提示安装命令行工具，或从官方安装入口选择方式。'),
        ('Ubuntu / Debian','使用系统包管理器：sudo apt update，然后 sudo apt install git。其他发行版按其官方方法安装。')])
    b.h('安装后只需配置一次')
    b.code('git --version\ngit config --global user.name "Your Name"\ngit config --global user.email "you@example.com"\ngit config --global init.defaultBranch main\ngit config --global --get user.name\ngit config --global --get user.email')
    b.p('把姓名和邮箱换成自己的。它们是提交的署名，**不会让你登录 GitHub**。希望提交关联账号时，用已在 GitHub 验证的邮箱；保护隐私可从 Settings → Emails 复制 GitHub 提供的 noreply 地址。')
    b.box('复制命令前先看约定','逐行执行命令，不复制提示符 $。OWNER、REPO、BRANCH、COMMIT 与 YOUR-NAME 都是示例占位词，使用时换成真实值。路径有空格时用英文双引号包住。')
    b.small('main 只是本书的示例主分支名。已有仓库可能叫 master 或其他名字，以仓库实际配置为准。')
    b.refs('02','28');b.end()

    b.start('连接方式 A：HTTPS 登录','推荐新手使用浏览器授权；GitHub 网站密码不能直接用作 HTTPS Git 操作密码。')
    b.h('方法 1：使用 GitHub CLI 的浏览器授权')
    b.p('从 cli.github.com 安装 GitHub CLI，再执行下列命令。它是额外工具，指令以 `gh` 开头；Git 指令仍以 `git` 开头。')
    b.code('gh --version\ngh auth login\ngh auth status')
    b.p('按提示选择 GitHub.com → HTTPS → 浏览器登录，并同意为 Git 配置身份验证。若仍未接通 Git 的凭据助手，可执行 `gh auth setup-git`。账号授权、仓库权限、远程地址三者都正确，才可以 push。')
    b.h('方法 2：使用系统凭据管理器或个人访问令牌')
    b.p('Git Credential Manager 等凭据助手可以引导你浏览器登录。若环境必须使用 PAT：在 GitHub 的 Settings → Developer settings → Personal access tokens 创建令牌，优先选细粒度令牌，并限制仓库、有效期与权限。')
    b.p('仅推送普通仓库内容时，通常需要所选仓库的 Contents 读写权限；组织审批、SSO、工作流文件或特殊操作可能另有要求。令牌不会给账号增加原本没有的仓库权限。')
    b.box('令牌的正确放法','在可信凭据管理器或工具的安全登录流程中使用。不要把令牌写进克隆 URL、代码、README 或命令截图。gh 通常使用系统凭据库；无法使用时可能回退为明文文件，可用 gh auth status 查看位置。',True)
    b.refs('04','30');b.end()

    b.start('连接方式 B：SSH 密钥','HTTPS 和 SSH 选一种即可；后续克隆地址必须与所选方式一致。')
    b.h('1. 检查并生成密钥（Git Bash / macOS / Linux）')
    b.code('ls -al ~/.ssh\nssh-keygen -t ed25519 -C "you@example.com"\neval "$(ssh-agent -s)"\nssh-add ~/.ssh/id_ed25519\ncat ~/.ssh/id_ed25519.pub')
    b.p('若已有可用密钥，可以复用；若提示覆盖现有文件，停止覆盖并改用新文件名。生成时建议设置口令。上述 ssh-add 与 cat 的路径应随自定义文件名修改。Windows 请在 Git Bash 中使用这组命令，不要与 PowerShell 代理步骤混用。')
    b.h('2. 上传公钥并测试')
    b.p('复制 `.pub` 文件的整行内容 → GitHub 个人 Settings → SSH and GPG keys → New SSH key → Authentication Key。私钥文件没有 .pub 后缀，保留在本机。')
    b.code('ssh -T git@github.com')
    b.p('首次连接先对照官方主机指纹页面，匹配后再输入 yes。出现 “successfully authenticated” 表示认证成功；“does not provide shell access” 属于正常说明，此测试退出码可能为 1。')
    b.box('macOS 口令记忆（可选）','Apple 自带 ssh-add 可使用 --apple-use-keychain。自动载入还需按官方文档配置 ~/.ssh/config；不要把这一 macOS 参数直接用于 Windows 或 Linux。')
    b.refs('05','06','07');b.end()

    b.start('不用命令行，先做一次网页练习','目标：理解“一个分支上的修改，通过 PR 合并到主分支”。')
    b.h('1. 新建仓库')
    b.p('在 GitHub 选择 New repository，命名 `github-practice`。练习可选 Private，勾选 Add a README file，点击 Create repository。Public 可被任何人查看；Private 由你授权访问。')
    b.h('2. 建分支并修改 README')
    b.p('在 Code 页的分支下拉框中，从 main 创建 `docs/intro`。打开 README.md，点击编辑，增加一句 “This is my GitHub practice repo.”，写清提交说明并 Commit changes 到该分支。')
    b.h('3. 发起 Pull Request')
    b.p('选择 Compare & pull request，或 Pull requests → New pull request。确认 base 是 main，compare 是 docs/intro。填写修改目的、内容与验证方式，创建 PR。')
    b.h('4. 检查并合并')
    b.p('阅读 Files changed，确认只改了预期内容。自己的练习仓库可自行合并；团队项目按审阅要求进行。合并后回 Code → main，确认新句子出现，再删除已完成的远程分支。')
    b.flow([('新建分支','隔离修改'),('Commit','保存说明'),('PR','提出与检查'),('Merge','纳入主分支')])
    b.box('怎么判断做成功了','main 上有新内容，PR 状态显示 Merged。网页上的提交已经保存在 GitHub；本地已有克隆时，仍需主动同步，文件不会自动改变。')
    b.refs('01','09');b.end()

    b.start('路线 A：克隆已有仓库','适合：仓库已经在 GitHub，包括刚刚创建的 github-practice。')
    b.p('打开仓库 Code 按钮，复制 HTTPS 或 SSH 地址。在希望存放项目的父目录打开终端；下面两种 clone 指令只执行其中一种。')
    b.code('# HTTPS\ngit clone https://github.com/YOUR-NAME/github-practice.git\n\n# SSH alternative\ngit clone git@github.com:YOUR-NAME/github-practice.git')
    b.h('进入目录，确认自己在哪里')
    b.code('cd github-practice\ngit status\ngit remote -v\ngit branch --show-current\ngit log --oneline -5')
    b.p('clone 通常会创建项目文件夹、下载版本历史、建立名为 origin 的远程连接，并检出默认分支。不需要再运行 git init 或再添加 origin。私有仓库需要先完成认证并获得权限。')
    b.table(['方式','应该怎样选择'],[
        ('Download ZIP','只拿文件快照，适合阅读。通常不含 .git，不能直接在原有历史上 pull / push。'),
        ('Clone','在电脑上继续开发、查看历史、同步修改。'),
        ('Fork','在 GitHub 上创建关联的独立仓库，适合没有原仓库写权限时贡献修改。之后仍可 clone。')])
    b.refs('03','08');b.end()

    b.start('路线 B：上传电脑里的项目','适合：电脑上已经有文件，但还没有对应的 GitHub 仓库。与路线 A 二选一。')
    b.h('1. 先在 GitHub 创建空仓库')
    b.p('创建名为 `my-project` 的仓库；这次不要勾选 README、.gitignore、License，以免产生两套独立初始历史。仓库创建成功后复制远程地址。')
    b.h('2. 在本地项目根目录初始化并检查')
    b.code('cd "PATH/TO/my-project"\ngit init -b main\ngit status')
    b.p('把路径换成自己的目录。先写 .gitignore 排除秘密和临时文件，再检查项目内容。下面先添加 README 与忽略规则；其他代码也要按真实路径添加，例如 git add main.py（文件确实存在时）。检查后再提交：')
    b.code('git add README.md .gitignore\n# Add other intended files by their actual paths\ngit diff --cached\ngit commit -m "Initial project structure"\ngit remote add origin https://github.com/YOUR-NAME/my-project.git\ngit remote -v\ngit push -u origin main')
    b.box('已有本地 Git 历史时','先用 git status 和 git remote -v 检查。不要为了“重新上传”删除 .git，也不要盲目改名已有分支。如果远程已含 README 等提交，较稳妥的入门方式是另处 clone，再复制项目文件并提交，保留双方需要的历史。')
    b.refs('03','24');b.end()

    b.start('保存一个版本：add 与 commit','一次提交最好只表达一个目的，例如“补充安装说明”。')
    b.p('用编辑器在 README.md 增加一段内容并保存。以下命令都在仓库目录中执行：')
    b.code('git status\ngit diff\ngit add README.md\ngit diff --cached\ngit commit -m "docs: add setup instructions"\ngit status\ngit log --oneline -5')
    b.table(['命令','你应该看见什么'],[
        ('git status','哪些文件新建、修改、删除，哪些已暂存；提交后应没有意外待提交内容。'),
        ('git diff','工作区相对暂存区的差异，即还没暂存的修改。'),
        ('git diff --cached','暂存区相对最近一次提交的差异，即这次 commit 将包含的内容。'),
        ('git commit','生成一个本地版本。通常显示提交哈希与文件变化摘要。')])
    b.box('为什么 add 之后还要再看一次','add 保存的是执行当时的内容。add 后又编辑文件，后续修改不会自动进入暂存区，要再次 add。git add . 会暂存当前目录及子目录的变化，用它之前一定先检查 status。')
    b.p('删文件也需记录：删除后对该路径执行 git add，或直接用 `git rm FILE`。改名可用 `git mv OLD NEW`。提交说明写“改了什么、为何要改”，避免只写 update。')
    b.refs('34','35','36');b.end()

    b.start('整理仓库：忽略规则与 README','先把项目解释清楚，也能减少误上传。')
    b.h('一份适合 Python / 数据作业起步的 .gitignore')
    b.code('.env\n.env.*\n!.env.example\n.venv/\nvenv/\n__pycache__/\n.ipynb_checkpoints/\n.DS_Store\nThumbs.db\n*.log')
    b.p('把这些行写入项目根目录的 .gitignore。它们是文件内容，不是终端命令。.env.example 只能保留变量名与虚构值；数据目录是否忽略，要按项目的共享方式决定。')
    b.box('被跟踪过的文件不会自动消失','如果 .env 已进入 Git，写入 .gitignore 后仍会被跟踪。可用 git rm --cached .env 停止后续跟踪，本地文件保留；再提交变更。旧提交依然含有它，若里面有秘密，立即撤销或更换秘密。',True)
    b.h('README 至少回答这五个问题')
    b.p('项目做什么？需要什么环境？怎样安装和运行？输入与输出是什么？遇到问题找哪里？建议补充目录结构、示例结果、数据来源与许可证。')
    b.code('# My Project\n## Goal\n## Setup\n## Run\n## Data and Results\n## License')
    b.small('Markdown 常用写法：# 标题、- 列表、**加粗**、[文字](链接)、三反引号围起代码块。License 规定复用条件；仓库公开并不等于任意使用。')
    b.refs('29','13','17');b.end()

    b.start('每天怎么同步与推送','先确认当前分支与工作区，再更新；push 发送的是提交，不是任意未提交文件。')
    b.h('最常用的日常节奏')
    b.code('git status\ngit branch --show-current\ngit pull --ff-only\n# Edit files, save, then review\ngit diff\ngit add README.md\ngit diff --cached\ngit commit -m "docs: clarify usage"\ngit push')
    b.p('前提：当前分支已经设置正确的上游跟踪关系；clone 得到的默认分支通常有。新分支第一次推送可用 `git push -u origin BRANCH`，之后再用 git push。团队若要求 PR，就把修改提交到功能分支。')
    b.h('fetch、pull、push 到底差在哪')
    b.table(['命令','效果'],[
        ('fetch','下载远程对象，更新本地的远程跟踪引用，通常不改当前工作文件。'),
        ('pull --ff-only','先 fetch，再只允许快进更新；本地与远程分叉时停止，避免自动做出合并选择。'),
        ('push','把本地指定分支的提交发送到远程；权限、分支保护或历史分叉可能使其失败。')])
    b.box('遇到“diverged / non-fast-forward”','先保存手头修改，再 fetch、查看提交图，判断应该 merge 还是按团队规范 rebase。不要把 --force 当成通用修复。功能分支的首次推送和后续更新，见手册第 6 页。',True)
    b.refs('23','24');b.end()

    b.start('用分支隔离一次修改','主分支保持可用，一项工作使用一个短期分支。分支不是复制一整个文件夹。')
    b.h('从最新主分支出发')
    b.code('git switch main\ngit pull --ff-only\ngit switch -c docs/usage\n# Edit README.md in your editor\ngit add README.md\ngit commit -m "docs: explain quick start"\ngit push -u origin docs/usage')
    b.p('开始前确保 git status 干净；有未完成修改时先提交或 stash。`switch -c` 创建并切换新分支；普通 switch 切换已有分支。分支名可用 feature/login、fix/read-csv、docs/usage，避免空格。')
    b.h('理解三个“看起来相似”的名字')
    b.table(['名称','含义'],[
        ('main','电脑里的本地主分支。'),('origin/main','本地保存的远程主分支状态，反映上次 fetch / 相关网络操作获知的远程位置。'),
        ('origin','远程地址的短名称，通常指你的克隆来源。'),('HEAD','当前检出的提交；通常通过当前分支指向它。')])
    b.box('在本地合并时，方向由当前分支决定','先 git switch main，再 git merge docs/usage，意思是把 docs/usage 纳入当前 main。团队仓库一般通过 GitHub PR 合并；不要为了练习在主分支上绕过规则。')
    b.refs('25','26');b.end()

    b.start('提交与合并 Pull Request','PR 是“请把这个分支的修改纳入目标分支”的协作请求。')
    b.h('1. 推送分支后，在网页创建 PR')
    b.p('选择 base: main，compare: docs/usage。写明目的、变化与验证结果。未完成可创建 Draft PR，需要审阅时再标记 Ready for review。')
    b.code('Title: docs: explain quick start\n\nWhy: New users need a minimal working example.\nChanges: Add setup and run steps to README.\nValidation: Followed the steps in a fresh environment.\nRelated issue: Closes #12')
    b.p('`Closes #12` 适用于确实解决该 Issue 的情况，并按 GitHub 关联与默认分支规则生效。不要为了套模板随意关闭别人的任务。')
    b.h('2. 审阅与更新')
    b.p('Files changed 检查差异；Checks 看自动检查；Review 中讨论问题。按意见在同一个本地分支继续修改、commit、push，原 PR 会更新，无需再开一个 PR。')
    b.h('3. 合并后同步本地')
    b.code('git switch main\ngit pull --ff-only\ngit branch -d docs/usage\ngit fetch --prune')
    b.box('合并方式会影响历史','Merge commit 保留分支合并结构；Squash 把该 PR 的修改合成一个提交；Rebase and merge 重新排列提交。遵循仓库规则。Squash 后 git branch -d 可能拒绝删除；先核对改动已入 main，详见手册第 5 页。')
    b.refs('09','32','33');b.end()

    b.start('处理合并冲突','冲突表示 Git 无法自动决定内容，需要你判断最终应保留什么。')
    b.p('场景：功能分支与 main 都改了 README 的同一行。工作区干净后，在功能分支合入最新 main：')
    b.code('git switch docs/usage\ngit fetch origin\ngit merge origin/main\ngit status')
    b.p('如果 README.md 出现下面标记，用编辑器整理成你真正需要的最终内容：')
    b.code('<<<<<<< HEAD\nRun with Python 3.11.\n=======\nRun with Python 3.12.\n>>>>>>> origin/main')
    b.p('在这个 merge 场景中，上半段来自当前功能分支，下半段来自 origin/main。按实际环境选择版本，删除全部冲突标记；先读内容，再决定是否使用“接受当前/传入”按钮。')
    b.code('git add README.md\ngit diff --cached\ngit commit -m "Merge main and resolve README conflict"\ngit push')
    b.box('如果暂时不想继续','在 merge 进行中可用 git merge --abort；最好在合并前保持工作区干净。若你是在 rebase 中冲突，暂存后应执行 git rebase --continue，放弃则 git rebase --abort，不能照抄 merge 的结束步骤。',True)
    b.refs('10','26');b.end()

    b.start('Fork：参与别人的项目','没有对方仓库的写权限时，在自己的仓库里修改，再向对方提交 PR。')
    b.h('建立 origin 与 upstream 两个方向')
    b.p('在原项目点 Fork，然后克隆自己名下的 Fork。这里 origin 指你的 Fork；upstream 指原项目。下面的 ORIGINAL-OWNER 也需要替换。')
    b.code('git clone https://github.com/YOUR-NAME/REPO.git\ncd REPO\ngit remote add upstream https://github.com/ORIGINAL-OWNER/REPO.git\ngit remote -v\ngit fetch upstream\ngit switch main\ngit merge --ff-only upstream/main\ngit push origin main\ngit switch -c fix/readme-typo')
    b.p('修改并 commit 后运行 `git push -u origin fix/readme-typo`。创建 PR 时检查三个位置：base repository 选原项目，head repository 选你的 Fork，compare 选功能分支。')
    b.box('同步 Fork 的好习惯','让 Fork 的 main 只跟随原项目，在独立功能分支工作。若 --ff-only 失败，说明本地 main 另有提交，应先检查；不要直接强制覆盖。网页也可用 Sync fork，同步后本地仍需 pull。')
    b.p('Fork 不会赋予你原仓库的写权限；原项目更新也不会自动进入你的 Fork。提交前阅读 CONTRIBUTING、许可证与维护者的约定。')
    b.refs('08','11');b.end()

    b.start('撤销：先判断修改在哪里','先执行 git status，再判断：未提交、已提交但未共享，还是已经推送给别人。')
    b.table(['你的目的','合适做法与影响'],[
        ('add 错了，想取消暂存','git restore --staged FILE：撤出暂存区，保留工作文件。已有首个提交时适用。'),
        ('不想要文件的未暂存修改','git restore FILE：工作文件回到暂存区版本，会丢掉该文件未暂存修改。'),
        ('撤回最近一次本地提交，保留内容','git reset --soft HEAD~1：分支退一条提交，改动留在暂存区；需确有父提交且尚未共享。'),
        ('撤销已推送的某次普通提交','git revert COMMIT：生成一个新的反向提交，通常更适合共享历史。先保证工作区干净。'),
        ('取回旧提交里的某个文件','git restore --source=COMMIT -- FILE：把旧版复制到工作区；检查后 add、commit。会覆盖该路径当前未提交内容。')])
    b.h('一个已经共享的错误，怎样修正')
    b.code('git status\ngit log --oneline -10\ngit revert COMMIT\n# Resolve conflicts if prompted, then verify\ngit push')
    b.box('先保留，再尝试','reset --hard、clean -fd、push --force 都可能造成难以恢复的结果。备份分支只保留提交，不保留未提交文件；后者需要提交、stash 或另外复制备份。合并提交的 revert 需要额外判断父分支，先查官方文档。',True)
    b.refs('18','19','20');b.end()

    b.start('临时收纳与找回提交','需要临时切换工作时用 stash；想找回过去的本地提交时看 reflog。')
    b.h('stash：先收起来，回头接着做')
    b.code('git stash push -u -m "WIP before switching tasks"\ngit stash list\n# Switch branches and finish the other task\ngit stash show -p "stash@{0}"\ngit stash apply "stash@{0}"\ngit status\n# Only after verifying the restored work\ngit stash drop "stash@{0}"')
    b.p('默认 stash 通常不含未跟踪文件；-u 会包含未跟踪文件，但不含已忽略文件。apply 保留 stash，确认恢复正常后再 drop；pop 会尝试恢复并在成功后删除该记录。stash 仍可能冲突。')
    b.h('reflog：找到“我刚才还在的那个提交”')
    b.code('git reflog --date=local\ngit show COMMIT\ngit branch rescue/recovered COMMIT\ngit log --oneline rescue/recovered -5')
    b.p('先确认正确提交，再建一个救援分支，之后再决定如何合并或取文件。这比直接 reset 到猜测的位置更易检查。')
    b.box('恢复能力有边界','reflog 是本机引用移动记录，不是远程备份，且会过期。它主要帮助找回曾经存在的提交；从未提交、从未暂存的文件被覆盖或删除后，Git 往往无法恢复。',True)
    b.refs('21','22');b.end()

    b.start('Issue、Review 与团队规则','用 Issue 讲问题，用 PR 讲改动，用 Review 检查改动是否解决问题。')
    b.h('一份可操作的 Issue')
    b.p('标题写具体，例如“空 CSV 会让导入脚本崩溃”。正文说明：复现步骤、期望结果、实际结果、环境版本、最小示例。截图和日志删去令牌、隐私与账号凭据。')
    b.table(['协作元素','建议用法'],[
        ('Labels / Assignees','标签区分 bug、docs、enhancement；负责人表示当前由谁跟进。'),
        ('Milestones / Projects','里程碑对应阶段目标，项目看板可按待做、进行中、完成管理任务。'),
        ('Review','审阅者看正确性、可维护性、测试与范围；作者回复每条有实质的问题。'),
        ('Rules / 分支保护','维护者可要求 PR、审阅或检查通过后合并，减少主分支误改。'),
        ('协作者权限','由仓库 Settings 中的访问管理邀请，给完成工作所需权限；不要共享账号或私钥。')])
    b.h('小团队可直接采用的约定')
    b.p('1. main 保持能运行；每项任务新建一个分支。\n2. 提交尽量小，PR 解释目的与验证方法。\n3. 合并前读差异、跑必要检查；重要修改由另一人审阅。\n4. 一个 PR 完成后及时同步 main，清理已完成分支。\n5. 公开项目补齐 README、LICENSE、CONTRIBUTING。')
    b.refs('16','17','09');b.end()

    b.start('Tag、Release 与 Pages','给稳定版本留路标，让别人知道该下载什么、在哪里看文档。')
    b.h('Tag：给某个提交取一个版本名')
    b.code('git switch main\ngit pull --ff-only\ngit tag -a v1.0.0 -m "First stable version"\ngit push origin v1.0.0\ngit tag --list\ngit show v1.0.0')
    b.p('先确认当前 main 就是要发布的内容。Tag 通常不随普通 git push 自动上传，需要显式推送。已发布版本不要随意移动标签；修复一般使用新的版本号。')
    b.h('Release：版本说明与可下载附件')
    b.p('在 GitHub 的 Releases → Draft a new release 选择已有标签，填写变化、使用方式和兼容性说明，可附带构建好的文件。Tag 是 Git 的版本标记；Release 是 GitHub 围绕版本组织的发布信息。')
    b.h('Pages：发布静态网页（可选）')
    b.p('示例：仓库中准备 index.html → Settings → Pages → 选择部署来源。若采用 Deploy from a branch，可选 main 与根目录，保存后查看部署状态；也可使用 GitHub Actions 发布。以设置页给出的最终网址为准。')
    b.box('适用范围','Pages 适合静态文档、个人主页、项目展示；Python 服务、数据库后端通常需要其他运行环境。可用性与仓库可见性受账号计划和组织规则影响，发布前检查站点是否会公开。')
    b.refs('15','38','42');b.end()

    b.start('Actions：自动运行检查','每次 push 或 PR 自动运行一段流程，减少“我电脑上能运行”的分歧。')
    b.p('先在练习仓库创建 `.github/workflows/hello.yml`，写入下方内容并提交、推送。这是认识工作流的最小例子，只打印信息，不测试项目代码。')
    b.code('name: Hello GitHub\non: [push, pull_request]\npermissions:\n  contents: read\njobs:\n  hello:\n    runs-on: ubuntu-latest\n    steps:\n      - name: Print message\n        run: echo "Hello from GitHub Actions"')
    b.h('如何读这份文件')
    b.table(['字段','含义'],[
        ('on','哪些事件触发流程；本例为 push 与 pull_request。'),('jobs','一组需要执行的任务。'),
        ('runs-on','在哪种运行环境执行；ubuntu-latest 为 GitHub 提供的 Ubuntu 运行器标签。'),
        ('steps','任务内逐步运行的操作；这里执行一句 echo。'),('permissions','限制工作流令牌权限，本例只给内容读取权限。')])
    b.p('打开 Actions 标签页，选择最新运行，查看任务和日志。真正测试代码时还需取出仓库代码、安装环境与依赖，再执行测试。可以从官方 workflow 模板起步，选择适合项目的版本。')
    b.box('读懂绿勾的含义','绿勾只说明这个流程中的步骤通过，不代表项目所有功能正确。运行器、权限、用量与计费可能受仓库和账号设置影响；秘密放在 Actions secrets 中，不要写进 YAML。')
    b.refs('14');b.end()

    b.start('数据项目、大文件与秘密','代码、配置样例和小型示例数据适合进仓库；原始大数据应先确定分发方式。')
    b.h('数据分析 / 机器学习项目的建议')
    b.p('提交代码、requirements.txt 或环境说明、随机种子、运行步骤和小型样例。大数据提供下载入口与校验信息；说明数据授权。Notebook 提交前检查输出，清除不需要的图像、日志与敏感数据。二进制文件通常难以逐行审阅和合并。')
    b.h('普通 Git 文件限制与 Git LFS')
    b.p('截至核对日期，GitHub 网页上传单文件不超过 25 MiB；普通 Git 中超过 50 MiB 会警告，超过 100 MiB 会被阻止。LFS 是单独的大文件存储机制，额度和限制需查看当前计划。')
    b.code('# Requires Git LFS to be installed separately\ngit lfs install\ngit lfs track "*.parquet"\ngit add .gitattributes\ngit add sample.parquet\ngit commit -m "Track sample data with LFS"\ngit push')
    b.p('track 要在把新文件提交进普通历史之前设置；它不会自动转换旧历史。若被拒的大文件已存在于旧提交，仅从当前目录删掉并再提交，通常仍无法解决。')
    b.box('如果令牌或私钥已经泄露','第一步立即撤销或更换秘密，再评估仓库历史、Fork、缓存和协作者克隆的清理。删除当前文件或改成 Private 不能保证泄露消失。历史重写需按官方流程协同处理。',True)
    b.refs('12','13','41');b.end()

    b.start('排错：登录、权限与网络','先定位是哪一层：地址 → 网络 → 身份 → 仓库权限 → 分支规则。')
    b.table(['现象','先检查与处理'],[
        ('Repository not found','git remote -v 看 OWNER/REPO 是否正确；浏览器登录后能否打开。私有仓库无权限时也可能显示找不到。'),
        ('Authentication failed','确认使用 HTTPS。重新走 gh auth login / 凭据助手；PAT 是否过期、被撤销或权限不足。不要使用网站密码。'),
        ('Permission denied (publickey)','确认使用 SSH。ssh -T git@github.com 检查认证账号；ssh-add -l 看代理是否加载正确密钥，公钥是否已加到该账号。'),
        ('403 / write access denied','认证成功不代表有写权限。确认登录账号、协作者邀请、组织 SSO / 审批以及令牌授权范围。'),
        ('Protected branch / required checks','按规则推送功能分支并开 PR；检查审阅、状态检查和分支保护要求。'),
        ('Timeout / Could not resolve host','先检查网络、域名解析、代理和 GitHub 服务状态。SSH 22 端口受限时可改用 HTTPS，或按官方文档使用 SSH over HTTPS。')])
    b.h('一组不修改历史的诊断命令')
    b.code('git remote -v\ngit branch -vv\ngh auth status\nssh -T git@github.com\nssh-add -l')
    b.small('gh 指令要求已安装 GitHub CLI。SSH 成功只验证账号认证；具体仓库仍需要相应读写权限。分享排错输出前删去访问令牌、私有 URL 和个人信息。')
    b.refs('03','04','06');b.end()

    b.start('排错：提交、分支与历史','尽量先查看状态和历史，再决定如何修改。')
    b.table(['提示或现象','原因与处理'],[
        ('not a git repository','你不在仓库目录。先 cd 进入 clone 出来的目录；不要在错误目录直接 init。'),
        ('src refspec main does not match any','可能还没有首个提交，或分支实际不叫 main。检查 git log、git branch --show-current，再创建提交或使用正确名称。'),
        ('remote origin already exists','已有 origin。先 git remote -v；地址确需更换时用 git remote set-url origin URL。'),
        ('nothing to commit','没有待提交变化，或未保存、修改了其他目录、文件被忽略。检查 git status --short 与 git check-ignore -v FILE。'),
        ('push 被 non-fast-forward 拒绝','远程有本地未包含的提交。先 fetch、查看提交图，再 merge 或按规范 rebase；不要直接强推。'),
        ('refusing to merge unrelated histories','本地与远程各自初始化。新手可另处 clone，再复制需要的文件提交；已有重要本地历史时先备份并另行规划合并。'),
        ('本地分支在 squash 合并后删不掉','git branch -d 无法确认祖先关系。先确认 PR 已合并且修改存在，再决定是否使用 -D。'),
        ('LF / CRLF 警告','多为换行符转换提醒。团队用 .gitattributes 统一文本规则，避免无意制造整文件差异。')])
    b.box('卡在编辑器或分页器时','git log / diff 常用 q 退出阅读。若 Git 打开了编辑器，按编辑器方式保存并退出：Vim 按 Esc 后输入 :wq 再回车；Nano 常用 Ctrl+O 保存、回车确认、Ctrl+X 退出。')
    b.refs('23','24','26','29');b.end()

    b.start('综合练习与验收清单','完成这一页，你就掌握了个人保存与基础协作的完整闭环。')
    b.h('练习任务：维护一份学习笔记')
    b.p('1. 创建带 README 的 github-practice 仓库，用选择的认证方式 clone。\n2. 从 main 新建 docs/study-plan 分支。\n3. 在 README 加上学习目标，在 .gitignore 写入临时文件规则。\n4. 用 status、diff 检查，按路径 add，再检查暂存差异并 commit。\n5. 首次 push 设置上游，创建 PR；写明变更与验证方法。\n6. 在网页检查差异并合并，回本地同步 main。\n7. 在单独练习分支修改一句话，尝试取消暂存；再用 stash 收起并恢复。\n8. 另用纯练习仓库制造一次双分支同一行冲突，解决后提交。')
    b.h('完成标准')
    b.table(['核验点','你应能回答'],[
        ('位置','目前在哪个仓库、哪个分支？工作区是否干净？'),('版本','哪个提交包含了这次修改？它是否已经推送？'),
        ('协作','PR 的目标分支正确吗？合并后 main 是否含有改动？'),('恢复','取消暂存和丢弃修改的命令有什么不同？'),
        ('边界','有没有上传令牌、大数据或不该公开的文件？')])
    b.box('建议的学习顺序','第一次：先完整做通流程，不追求记住全部指令。第二次：遇到问题先查手册。第三次：再学 rebase、cherry-pick、bisect 等专题。掌握基础闭环比一次记住很多参数更有用。')
    b.end()

    b.start('术语对照与学习建议','用词先对齐，看到英文提示时就不容易慌。')
    b.table(['英文','中文与含义'],[
        ('Working tree / Index','工作区 / 暂存区：正在编辑的文件 / 准备进入下次提交的内容。'),
        ('Tracked / Untracked','已跟踪 / 未跟踪：Git 已管理的路径 / 尚未纳入版本管理的路径。'),
        ('HEAD / Commit hash','当前检出位置 / 提交唯一标识；短哈希需能在该仓库中唯一辨认。'),
        ('Remote / origin','远程连接 / 常见远程短名称；名字本身不带特殊权限。'),
        ('Upstream branch','本地分支的跟踪目标。与 Fork 流程中名为 upstream 的远程是两个概念。'),
        ('Merge / Rebase','合并 / 变基：两种整合历史的方式；rebase 会重建被重放的提交。'),
        ('Fast-forward / Diverged','快进 / 分叉：能直接前移指针 / 两侧都有对方尚未包含的提交。'),
        ('PR / Review / Conflict','合并请求 / 审阅 / 冲突：提出修改 / 检查修改 / 自动整合需要人工判断。'),
        ('Fork / Clone','GitHub 上的关联独立仓库 / 下载到本机的 Git 仓库副本。'),
        ('Tag / Release / CI','版本标签 / 发布说明与附件 / 持续集成检查。')])
    b.p('配套手册按任务查找，涵盖常用指令与风险说明。需要完整选项时，使用 `git help COMMAND`、`git COMMAND -h` 或 `gh COMMAND --help`，把 COMMAND 换成实际子命令。')
    b.small('本教程按 2026-10-31 可访问的官方文档核对。GitHub 页面名称、计划限制、组织策略与软件版本可能变化；以实际界面和官方参考为准。本文为独立中文教学材料。')
    b.end()

    b.start('官方参考资料 A','各教学页的“官方参考”可直接点击；以下汇总便于继续学习。')
    b.sources(['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15'])
    b.end()
    b.start('官方参考资料 B','Git 命令有完整官方说明；GitHub CLI 与 Git 是不同工具。')
    b.sources(['16','17','18','19','20','21','22','23','24','25','26','27','28','29'])
    b.small('补充条目：Git add / commit / diff / log / tag 官方手册、Git LFS 与 Release 管理，可点击对应教学页中的参考链接。GitHub CLI：cli.github.com/manual。')
    b.end()
    return b.save()

def build_manual():
    b=Book('Git与GitHub_指令速查使用手册.pdf','Git 与 GitHub 指令速查使用手册','REFERENCE',15)
    b.start('Git / GitHub 指令速查','按任务查找，逐行执行。含常用指令、适用前提和高风险操作说明。','REFERENCE  /  2026.10.31')
    b.box('使用前先看这四条','① 在正确仓库目录执行，先看 git status。② OWNER、REPO、BRANCH、FILE、COMMIT、URL 都要替换。③ 示例主分支为 main，已有仓库以实际名称为准。④ Git Bash / macOS / Linux 可直接使用本书 Shell 写法；不要把命令里的 # 注释和配置文件内容混淆。')
    b.toc([(2,'安装、身份与登录',''),(3,'创建、克隆与远程地址',''),(4,'查看、暂存、提交与历史',''),
           (5,'分支、合并与清理分支',''),(6,'拉取、推送与同步 Fork',''),(7,'冲突处理：继续还是放弃',''),
           (8,'撤销决策：先判断修改位置',''),(9,'stash、reflog 与找回文件',''),(10,'进阶与高风险操作',''),
           (11,'GitHub CLI：仓库、Issue、PR',''),(12,'Tag、Release、LFS 与忽略规则',''),
           (13,'报错速查',''),(14,'三张可复用的流程卡',''),(15,'官方资料与更多帮助','')])
    b.h('风险标记')
    b.p('**查看**：主要读取信息。**改动**：会修改本地或远程状态。**谨慎**：可能覆盖文件、删除内容或改写历史。操作说明比标记更重要。')
    b.small('本手册配套完整教程使用，也可独立查阅。PDF 书签和目录支持跳转；后续页的页脚标题可返回此页。')
    b.end()

    b.start('安装、身份与登录','Git 管理版本，gh 操作 GitHub；gh 需要单独安装。')
    b.table(['指令','用途与前提'],[
        ('git --version','查看：确认 Git 可用及当前版本。'),
        ('gh --version','查看：确认 GitHub CLI 已安装。'),
        ('git config --global user.name "Your Name"','改动：设置提交姓名，并非登录账号。'),
        ('git config --global user.email "you@example.com"','改动：设置提交邮箱；改用自己的已验证邮箱或 GitHub noreply 地址。'),
        ('git config --global init.defaultBranch main','改动：设置以后初始化仓库的默认分支名，不改已有仓库。'),
        ('git config --show-origin --get user.email','查看：找出当前生效邮箱与配置来源。'),
        ('gh auth login','改动：浏览器授权，选择 GitHub.com 与 HTTPS，再为 Git 配置登录。'),
        ('gh auth setup-git','改动：让 Git 使用 gh 的凭据助手；先完成 gh 登录。'),
        ('gh auth status','查看：登录的主机、账号及凭据状态。'),
        ('git help COMMAND','查看：完整命令帮助，例如 git help push。')], [CW*.56,CW*.44],True)
    b.box('配置的范围','--global 影响当前用户的仓库；去掉 --global 通常写入当前仓库配置，可用于工作 / 个人身份分别设置。HTTPS 不接受 GitHub 网站密码；PAT 要限制权限与有效期。')
    b.small('安装入口：git-scm.com、cli.github.com。Windows 建议统一使用 Git Bash；SSH 完整初始配置见教程第 7 页。')
    b.refs('02','04','28','30');b.end()

    b.start('创建、克隆与远程地址','clone 是从现有仓库开始，init 是为已有本地目录建立仓库，通常二选一。')
    b.table(['指令','用途与前提'],[
        ('git clone URL','改动：克隆已有仓库到新目录；URL 从 GitHub Code 按钮复制。'),
        ('cd "PATH/TO/REPO"','切换目录；这是终端命令，不是 Git 子命令。'),
        ('git init -b main','改动：在当前目录初始化；先确认目录正确。'),
        ('git status','查看：分支与文件状态，也是操作前的起点。'),
        ('git rev-parse --show-toplevel','查看：当前仓库根目录。'),
        ('git remote -v','查看：远程短名称、获取与推送地址。'),
        ('git remote add origin URL','改动：添加远程；若 origin 已存在，先查看，不重复添加。'),
        ('git remote set-url origin URL','改动：修改已有 origin 的地址。'),
        ('git remote rename origin old-origin','改动：重命名远程；通常不需要。'),
        ('git remote remove old-origin','改动：移除本地远程配置，不会删除 GitHub 仓库。')], [CW*.55,CW*.45],True)
    b.h('两种地址格式')
    b.code('https://github.com/OWNER/REPO.git\ngit@github.com:OWNER/REPO.git')
    b.small('上传已有项目：先在 GitHub 建空仓库 → 本地 init → 写忽略规则 → add / commit → remote add → push -u。网页若已创建 README，建议先 clone，再复制文件提交。')
    b.refs('03','08','31');b.end()

    b.start('查看、暂存、提交与历史','add 选择下次提交内容；commit 保存本地版本；push 才上传提交。')
    b.table(['指令','用途与注意事项'],[
        ('git status --short','查看：M 修改、A 新增已暂存、D 删除、?? 未跟踪；两列区分暂存与工作区。'),
        ('git diff','查看：工作区与暂存区的差异，不列出未跟踪文件内容。'),
        ('git diff --cached','查看：暂存区与 HEAD 的差异，即这次提交内容。'),
        ('git diff HEAD','查看：已跟踪文件相对 HEAD 的整体变化，含已暂存和未暂存。'),
        ('git add FILE1 FILE2','改动：按路径暂存新建、修改或删除。'),
        ('git add -p FILE','改动：按差异块交互选择；适合拆分已有文件修改。'),
        ('git add .','改动：暂存当前目录及子目录变化；先检查不要混入秘密或无关文件。'),
        ('git commit -m "Explain the change"','改动：提交暂存内容；署名与邮箱需已配置。'),
        ('git log --oneline -10','查看：最近十条提交及短哈希。'),
        ('git log --oneline --graph --all --decorate','查看：分支与提交图。'),
        ('git show COMMIT','查看：某个提交的说明与修改。'),
        ('git log --follow -- FILE','查看：追踪单文件历史，尝试跟随改名。')], [CW*.56,CW*.44],True)
    b.small('分页阅读用 q 退出。add 后再次编辑文件，必须再次 add 才能把后续修改放入同一次 commit。')
    b.refs('34','35','36','37');b.end()

    b.start('分支、合并与清理分支','开始前保持工作区干净。merge 的接收方始终是当前分支。')
    b.table(['指令','用途与注意事项'],[
        ('git branch --show-current','查看：当前分支名；分离 HEAD 时可能为空。'),
        ('git branch -vv','查看：本地分支、上游及提交位置。'),
        ('git branch -a','查看：本地和远程跟踪分支。'),
        ('git switch -c feature/topic','改动：从当前提交创建并切换分支。'),
        ('git switch BRANCH','改动：切换本地已有分支。'),
        ('git switch --track origin/BRANCH','改动：从远程跟踪分支创建对应本地分支并跟踪；本地尚无该分支时使用。'),
        ('git branch -m NEW-NAME','改动：重命名当前本地分支，不会自动重命名 GitHub 分支。'),
        ('git merge feature/topic','改动：将功能分支合入当前分支；团队主分支通常通过 PR 合并。'),
        ('git branch -d feature/topic','改动：尝试删除已合并的本地分支；先切到其他分支。'),
        ('git push origin --delete feature/topic','谨慎：删除远程分支；先确认不再需要。'),
        ('git fetch --prune','改动：更新远程状态并清理已不存在的远程跟踪引用；不删除对应本地分支。')], [CW*.56,CW*.44],True)
    b.box('Squash 合并后为什么 -d 可能失败','Git 无法仅凭祖先关系认出 squash 后的修改。先确认 PR 已合并、main 已更新且改动完整，再决定 git branch -D feature/topic；-D 会跳过未合并保护，不能盲用。',True)
    b.refs('25','26','24');b.end()

    b.start('拉取、推送与同步 Fork','先确认当前分支和跟踪目标。pull 会整合到当前分支，不会自动切换分支。')
    b.table(['指令','用途与前提'],[
        ('git fetch origin','改动：获取远程更新与跟踪状态，通常不改工作文件。'),
        ('git pull --ff-only','改动：仅允许快进更新当前跟踪分支；分叉时停止。'),
        ('git pull --ff-only origin main','改动：把远程 main 快进到当前分支；应先切到你打算更新的分支。'),
        ('git push -u origin BRANCH','改动：首次推送分支并设置上游。'),
        ('git push','改动：按已有上游与配置推送当前分支。'),
        ('git branch --set-upstream-to=origin/BRANCH','改动：为当前分支设置已有远程跟踪目标。'),
        ('git log --oneline HEAD..origin/main','查看：origin/main 有、当前 HEAD 没有的提交。'),
        ('git log --oneline origin/main..HEAD','查看：当前 HEAD 有、origin/main 没有的提交。')], [CW*.58,CW*.42],True)
    b.h('同步自己的 Fork（main 未加入个人提交时）')
    b.code('git remote add upstream https://github.com/OWNER/REPO.git\ngit fetch upstream\ngit switch main\ngit merge --ff-only upstream/main\ngit push origin main')
    b.small('upstream 远程只需添加一次；OWNER/REPO 指原项目，origin 指自己的 Fork。--ff-only 失败先查看历史。功能改动放在其他分支，再向原项目开 PR。')
    b.refs('23','24','11');b.end()

    b.start('冲突处理：继续还是放弃','先 git status，看清自己正在 merge、rebase、cherry-pick 还是 revert。')
    b.h('共同步骤')
    b.code('git status\ngit diff --name-only --diff-filter=U\n# Edit each conflicting file; remove conflict markers\ngit add FILE\ngit diff --cached')
    b.p('阅读冲突双方内容，整理成最终结果；删掉 <<<<<<<、=======、>>>>>>> 标记。若最终决定删除冲突文件，用 `git rm FILE` 记录删除。再按当前操作选择结束方式：')
    b.table(['正在做什么','解决后继续','放弃本次操作'],[
        ('merge','git commit','git merge --abort'),('rebase','git rebase --continue','git rebase --abort'),
        ('cherry-pick','git cherry-pick --continue','git cherry-pick --abort'),
        ('revert','git revert --continue','git revert --abort')], [CW*.22,CW*.39,CW*.39])
    b.h('功能分支纳入远程主分支的例子')
    b.code('git switch feature/topic\ngit fetch origin\ngit merge origin/main\n# If conflicted: edit, git add FILE, git commit\ngit push')
    b.box('两个不要混用的概念','merge 与 rebase 冲突中，“ours / theirs” 的直觉可能不同；直接读内容更可靠。--skip 会跳过当前正在应用的提交，可能丢掉该提交的效果，不是通用“解决冲突”按钮。',True)
    b.refs('10','26','40','39','20');b.end()

    b.start('撤销决策：先判断修改位置','高风险命令不要按习惯粘贴。先看 status、diff 与提交是否已经共享。')
    b.table(['想做什么','指令与影响'],[
        ('取消暂存，保留编辑','git restore --staged FILE\n已有 HEAD 时使用；初始仓库尚无提交时可用 git rm --cached FILE 取消首次跟踪。'),
        ('丢弃指定文件未暂存修改','git restore FILE\n谨慎：工作区被暂存区内容覆盖，丢弃的未提交修改可能无法恢复。'),
        ('取出旧版文件','git restore --source=COMMIT -- FILE\n谨慎：覆盖该路径工作文件；不会直接创建提交。'),
        ('撤回最后一次未共享提交，内容仍暂存','git reset --soft HEAD~1\n谨慎：分支退一条；需存在父提交且未共享。'),
        ('撤回最后一次未共享提交，内容不暂存','git reset --mixed HEAD~1\n谨慎：重置暂存区，工作文件保留；同样需存在父提交。'),
        ('修正最近一次未共享提交说明','git commit --amend -m "New message"\n谨慎：生成新提交；当前暂存内容也会纳入。只改说明时先确认暂存区无其他改动。'),
        ('撤销已共享普通提交的效果','git revert COMMIT\n改动：新建反向提交；工作区应干净，可能冲突。'),
        ('暂时停止跟踪文件，本地保留','git rm --cached FILE\n改动：下一次提交记录停止跟踪；通常还需补 .gitignore。历史不会因此清除。')], [CW*.31,CW*.69])
    b.box('共享历史优先用 revert','本地且未共享时可以考虑 reset / amend；共享后用反向提交通常更便于协作。合并提交的 revert 需要判断主线父提交，不要随意加 -m 1。')
    b.refs('18','19','20','35');b.end()

    b.start('stash、reflog 与找回文件','stash 暂存未完成工作；reflog 帮你查本机引用曾经指到的提交。')
    b.table(['指令','用途与注意事项'],[
        ('git stash push -u -m "WIP"','改动：收起已跟踪修改与未跟踪文件；不含已忽略文件。'),
        ('git stash list','查看：stash 列表，最新通常是 stash@{0}。'),
        ('git stash show -p "stash@{0}"','查看：指定 stash 的差异；加 --include-untracked 可同时查看其中未跟踪文件。'),
        ('git stash apply "stash@{0}"','改动：应用且保留记录，可能冲突；默认不保证恢复原暂存状态。'),
        ('git stash apply --index "stash@{0}"','改动：尝试同时恢复暂存状态，仍可能失败或冲突。'),
        ('git stash pop','改动：应用最新记录并在成功后移除；冲突时通常保留记录。'),
        ('git stash drop "stash@{0}"','谨慎：删除这条 stash；先确认内容已恢复。'),
        ('git reflog --date=local','查看：本机 HEAD / 引用移动的历史线索。'),
        ('git branch rescue/recovered COMMIT','改动：为找到的提交建立救援分支，不直接覆盖当前工作区。'),
        ('git restore --source=COMMIT -- FILE','谨慎：恢复该路径旧内容到工作区，核对后再 add / commit。')], [CW*.57,CW*.43],True)
    b.box('备份的边界','分支只保留提交；普通 stash 不含忽略文件。reflog 会过期且主要记录本机活动。数据库、未跟踪文件和从未保存的编辑，仍需适当文件备份。',True)
    b.refs('21','22','18');b.end()

    b.start('进阶与高风险操作','只在确认前提后使用。共享分支上的历史调整先与协作者约定。')
    b.h('整合或整理提交')
    b.table(['指令','适用情形'],[
        ('git rebase origin/main','谨慎：把当前功能分支提交重放到最新主分支之上；先 fetch、保持工作区干净，会重建提交。'),
        ('git cherry-pick COMMIT','改动：把某个普通提交的改动应用到当前分支，通常形成新提交；可能冲突。'),
        ('git rebase -i HEAD~3','谨慎：交互整理最近三条提交；需足够父提交，一般仅整理自己未共享的历史。'),
        ('git push --force-with-lease origin BRANCH','谨慎：重写自己的远程分支；比 --force 多一层预期状态检查，仍可覆盖已知远程提交。')], [CW*.57,CW*.43],True)
    b.small('--force-with-lease 不是绝对保险。默认判断依赖本地远程跟踪状态；后台 fetch 可能削弱这层保护。确认待覆盖提交、保留恢复路径，只在确实需要重写历史时使用。')
    b.h('丢弃或清理（先备份、先预览）')
    b.code('git branch backup/before-reset\ngit status\ngit reset --hard COMMIT\n\ngit clean -nd -- PATH\ngit clean -fd -- PATH')
    b.box('明确会失去什么','reset --hard 覆盖已跟踪工作内容和暂存区，并可能移除挡路的未跟踪路径；备份分支不保留未提交编辑。clean -fd 删除所选路径下的未跟踪文件 / 目录，默认不删忽略项。先 -nd 预览并另备份需要的文件。-x 还会包含忽略项，通常不要随意加。',True)
    b.refs('19','24','27','39','40');b.end()

    b.start('GitHub CLI：仓库、Issue、PR','所有 gh 指令要求已安装并登录；不带 -R 时通常根据当前仓库推断目标。')
    b.table(['指令','用途与前提'],[
        ('gh repo view --web','查看：在浏览器打开当前 GitHub 仓库。'),
        ('gh repo clone OWNER/REPO','改动：克隆 GitHub 仓库到本地。'),
        ('gh repo create REPO --private --clone','改动：在当前登录账号下创建私有仓库并克隆到新目录。'),
        ('gh issue list','查看：列出仓库 Issue。'),
        ('gh issue view 12 --web','查看：在网页打开 #12。'),
        ('gh issue create --web','改动：打开浏览器填写新 Issue。'),
        ('gh pr list','查看：列出 PR。'),
        ('gh pr create --base main --web','改动：为当前功能分支打开 PR 创建页面；先 commit / push，确认 base 与 head。'),
        ('gh pr checkout 12','改动：检出 #12 的代码到本地；先保存当前修改。'),
        ('gh pr diff 12','查看：阅读 #12 的改动。'),
        ('gh pr checks 12','查看：检查状态。'),
        ('gh pr view 12 --web','查看：网页阅读 PR、审阅和合并。')], [CW*.59,CW*.41],True)
    b.small('已读差异、测试通过且具备权限时，可用 gh pr merge 12 --squash --delete-branch 合并并清理分支；受仓库规则与队列策略限制，可能暂不完成合并。编号 12 要替换。')
    b.refs('30','31','32','33');b.end()

    b.start('Tag、Release、LFS 与忽略规则','先确认当前提交和目标仓库，标签推送与 Release 创建会改变远程状态。')
    b.table(['指令','用途与注意事项'],[
        ('git tag -a v1.0.0 -m "Stable"','改动：给当前提交建立附注标签。'),('git tag --list','查看：列出本地标签。'),
        ('git push origin v1.0.0','改动：推送指定标签；普通 push 不保证上传标签。'),
        ('gh release create v1.0.0 --verify-tag','改动：基于已存在远程标签交互创建 Release。'),
        ('git lfs install','改动：初始化已另行安装的 LFS；通常每个用户环境一次。'),
        ('git lfs track "*.parquet"','改动：写入 LFS 跟踪模式；随后提交 .gitattributes 及对应新文件。'),
        ('git lfs ls-files','查看：仓库内由 LFS 跟踪的文件。'),
        ('git check-ignore -v FILE','查看：文件命中了哪条忽略规则；已跟踪文件默认不显示。'),
        ('git ls-files','查看：当前索引中的已跟踪路径。'),
        ('git rm --cached FILE','改动：停止跟踪但保留本地文件；旧历史仍在。')], [CW*.56,CW*.44],True)
    b.h('写在配置文件里的内容，不是终端命令')
    b.p('`.gitignore` 每行一条：.env、.venv/、__pycache__/、*.log。若用 !.env.example 取消忽略，示例文件只能写虚构值。`.gitattributes` 可按团队约定使用 `* text=auto`，特定文本文件再指定 `eol=lf`。')
    b.small('LFS 的 track 不迁移既有历史。大文件已进入旧提交时需单独处理；额度与计费看当前计划。公开内容还应有合适的许可证和数据授权说明。')
    b.refs('38','42','41','29');b.end()

    b.start('报错速查','先用 git status、git remote -v、git branch -vv 确认现场。')
    b.table(['关键词 / 现象','优先处理'],[
        ('not a git repository','进入仓库根目录；检查 git rev-parse --show-toplevel。'),
        ('Authentication failed','HTTPS 凭据问题。重新授权，检查 PAT 有效期和权限；不能用网站密码。'),
        ('Permission denied (publickey)','SSH 问题。看 ssh -T git@github.com 与 ssh-add -l，确认公钥所属账号。'),
        ('Repository not found / 403','检查 OWNER/REPO、登录账号、仓库权限及组织授权。'),
        ('remote origin already exists','先 remote -v；需换地址用 remote set-url，不重复 add。'),
        ('src refspec ... does not match any','检查是否有首个提交、分支名是否拼对。'),
        ('non-fast-forward / diverged','fetch 后看历史图；选择合适 merge / rebase，不直接强推。'),
        ('would be overwritten','先提交、stash 或备份当前修改，再切分支 / 拉取。'),
        ('unrelated histories','两边各自初始化。新手可另处 clone，再复制所需文件提交；保留重要历史需另行规划。'),
        ('file exceeds 100 MiB','普通 Git 大文件限制；考虑 LFS，并检查旧提交是否已含该文件。'),
        ('detached HEAD','当前不在分支上。若要保留新提交，先 git switch -c rescue/my-work。'),
        ('编辑器 / log 不知道怎么退出','log / diff 用 q；Vim 用 Esc、:wq、回车；Nano 常用 Ctrl+O、回车、Ctrl+X。')], [CW*.39,CW*.61])
    b.small('网络超时先查网络、DNS、代理和服务状态。不要通过关闭 TLS 验证或公开凭据来“修复”连接。')
    b.refs('03','04','06','12','23');b.end()

    b.start('三张可复用的流程卡','每一段都先满足前提；编辑文件的步骤需要你在编辑器里完成。')
    b.h('A. 从已有仓库开始（新电脑 / 新目录）')
    b.code('git clone https://github.com/OWNER/REPO.git\ncd REPO\ngit status\ngit switch -c feature/topic')
    b.h('B. 功能分支提交与创建 PR')
    b.code('git status\ngit diff\ngit add FILE\ngit diff --cached\ngit commit -m "Explain the change"\ngit push -u origin feature/topic\ngh pr create --base main --web')
    b.h('C. PR 合并后收尾')
    b.code('git switch main\ngit pull --ff-only\ngit branch -d feature/topic\ngit fetch --prune')
    b.box('执行条件','A 中 topic 分支名换成实际名称。B 的 FILE 可以列出多个路径；gh 未安装时在网页建 PR。C 中 -d 若因 squash 合并而拒绝，先核实 PR 与改动，按第 5 页处理。每次新任务从更新后的 main 新建分支。')
    b.small('最常用记忆顺序：status → diff → add → diff --cached → commit → push。拿不准撤销时，先停在查看步骤并查第 8 页。')
    b.end()

    b.start('官方资料与更多帮助','核对日期：2026-10-31。以下是原始参考入口；完整教程末尾有更多主题链接。')
    b.sources(['02','03','04','18','19','20','21','22','23','24','29','30','31','32','33'])
    b.small('补充官方入口：git-scm.com/docs（所有 Git 子命令）、cli.github.com/manual（所有 gh 子命令）、docs.github.com（GitHub 功能）。各功能页也附有直接参考链接。')
    b.end()
    return b.save()

if __name__=='__main__':
    results=[build_tutorial(),build_manual()]
    (TMP/'build_report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(json.dumps(results,ensure_ascii=False,indent=2))
