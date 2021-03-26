Gerrit 登录地址

http://192.168.202.24/gerrit/c/MCS-horizon

用户名: 姓名全拼

初始密码: comleader@123



**点设置**

用户第一次登录请设置邮箱，验证邮箱



**设置公钥(新生成或者查看)**

1. 查看公钥

```
cat ~/.ssh/id_rsa.pub 
```

2. 生成公钥

```
ssh-keygen -t tsa
```



**在命令行执行下面的命令**，就可以把MCS-horizon工程给clone下来了

```
$ git clone "ssh://your_name@192.168.202.24:29418/MCS-horizon" && scp -p -P 29418 your_name@192.168.202.24:hooks/commit-msg "MCS-horizon/.git/hooks/"
```





## 提交

首先我们通过下面两个命令首先commit到本地仓库：

```
$ git add .  # 提交所有变更
$ git commit -m '本地提交信息'
$ git push origin HEAD:refs/for/master
```

可能会提示配置，设置全局变量

```
$ git config user.name your_name
$ git config user.email your_name@comleader.com.cn
```



合并master提示

```
 git push origin HEAD:refs/for/master
报错
  ! [remote rejected]   HEAD -> refs/for/master (commit 0a1dc25: missing Change-Id in message footer)
  根据git提示信息：
gitdir=$(git rev-parse --git-dir); 
scp -p -P 29418 your_name@192.168.202.24:hooks/commit-msg ${gitdir}/hooks/
git commit --amend --no-edit
及 参考链接：https://stackoverflow.com/questions/59470484/git-push-failed-due-to-change-id
 
最终执行命令
scp -p -P 29418 your_name@192.168.202.24:hooks/commit-msg ".git/hooks/"
git commit --amend
push成功
```

成功后

指定 Code-Review     Verified审核人员，对应评分

submit提交到gerrit服务器，服务器会自动同步到gitlab





## 合并到develop分支流程

本地分支dev_yjz

先拉去自己的本地分支，```git pull origin dev_yjz```

开发代码，开发完成后，```git add . ```      ```git commit -m '开发内容解释'```

切换到本地develop分支

#### 两种方式：

#### 方式一：**(优先用这种)**

合并时在develop生成新的commit信息

```
git merge dev_yjz --no-ff
git push origin HEAD:refs/for/develop
```

 --no-ff：不使用fast-forward方式合并，合并的时候会创建一个新的commit用于合并。

#### 方式二：

先合并，合并后amend到该分支上次提交的信息中

```
git merge dev_yjz
git commit --amend
git push origin HEAD:refs/for/develop
```







### 配置创建Change的便捷命令

```
#原理是使用git的别名功能将复杂的命令和参数进简化
#创建pushdev和pushmaster别名
git config --global alias.pushdev "push origin HEAD:refs/for/develop"
git config --global alias.pushmaster "push origin HEAD:refs/for/master"

#别名创建完成后，可以使用
git pushdev
#代替
git push origin HEAD:refs/for/develop

#可以使用
git pushmaster
#代替
git push origin HEAD:refs/for/master
```



参考链接：http://gitlab.aotimes.com/root/readme/blob/master/Gerrit%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E.md













### 问题1

遇到如下问题：

```
To ssh://192.168.202.24:29418/MCS-horizon
 ! [remote rejected]   HEAD -> refs/for/develop (Pushing merges in commit chains with 'all not in target' is not allowed,
to override please set the base manually)
error: failed to push some refs to 'ssh://192.168.202.24:29418/MCS-horizon'

```

**解决**

You do NOT need to abandon the current change on Gerrit to solve the "cannot merge" issue. All you need to do is:

Update your local repository (git fetch)
Run a manual rebase (git rebase)
Resolve the conflicts (git mergetool, git rebase --continue)
Commit (amend) the result (git commit --amend)
Push a new patchset to Gerrit (git push)

参考链接：https://stackoverflow.com/questions/37583710/cannot-merge-in-gerrit/37590769



### 问题2

**gerrit "missing Change-Id"**

**解决**

使用交互式 rebase 找回任意提交位置的 Change-Id:

第一步,找到缺失 Change-Id 的那个 commit:

第二步,编辑交互式 rebase 的命令文件:

执行 git rebase -i, 参数为 该提交的上一个提交的 commit-id

$ git rebase -i d714bcde0c14ba4622d28952c4b2a80882b19927
这个命令会打开默认的编辑器,一般为 vi. 内容如下:

pick 1a9096a I am commit message 1
pick 8e1cad3 I am commit message 2
pick 8aaaa74 I am commit message 3

可以将这个文件理解为 git rebase 的内嵌脚本.其命令写法已经在下面的注释里给出了.

这里不赘述,仅给出最终要将该文件编辑成什么样子:

reword 1a9096a I am commit message 1
pick 8e1cad3 I am commit message 2
pick 8aaaa74 I am commit message 3

即: 将缺失了 Change-Id 的 commit 前面的 "pick" 改为 "reword" 即可. 保存退出 (:wq)

注1: 上述文件中 commit 的顺序是和 git log 显示的顺序相反的: git log 为最新的在最前; 上述文件为 最新的在最后.

注2: 如果进入该模式后,却不确定该怎么改,这时不要担心,直接退出编辑则什么都不会发生 (:q!)

注3: 如果没有搞清楚运作机制,就要注意,除了按需把 pick 改为 reword 外,不要做其他改动.尤其注意不要删除任何行 (被删除的那行对应的提交将丢失).

注4: 你应该已经发现,有多个 commit 缺失 Change-Id 的情况也可以用该方法一次性处理.



第三步,逐个编辑 commit-msg:

上一步打开的文件保存退出后,git会逐个打开被你标注了 reword 的提交日志页面.

不需要修改任何东西,逐个保存退出即可 (一路 :wq).



第四步,再次提交:

$ git push review HEAD:refs /for/master
参考链接：https://blog.csdn.net/liuxu0703/article/details/54343096





### 问题3

**gerrit push (change closed)解决办法**

出现原因：gerrit上一个change的已经关闭了，这时候从其他分支merge进来的内容没有commit成一个新的提交点，没有生成新的changeId,继续沿用上一个提交changId
解决方法：
git checkout -b 新分支
git merge --squash 需要合并的分支
git commit -m 'xxx'
git push origin HEAD:refs/for/test

参考链接：https://blog.csdn.net/RuiClear/article/details/109447874



### 问题4

```
   remote rejected
   commit subject >65 characters; use shorter first paragraph
```

原因是某个提交的commit message太多，导致原因之一是在gerrit中有abandon的提交，

把abandon的提交都删除，重新提交试一下，如果不行，看下面的方法

见下面示例messge4后面的内容

```
ick 1a9096a I am commit message 1
pick 8e1cad3 I am commit message 2
pick 8aaaa74 I am commit message 3
pick aagffsd I am commit message4 sadfsal;fjas;fjf;lsakfjas;lfkjsflksjf;slkfjsad;lfkasf;skjfs;alfjsdfjsfljsdf;lksdjf;slfjsd;lfjsdflf;fk
pick 8asdfa74 I am commit message 5
pick 34aasdf I am commit message 6
# Rebase d714bcd..8aaaa74 onto d714bcd
# Commands:
#  p, pick = use commit
#  r, reword = use commit, but edit the commit message
#  e, edit = use commit, but stop for amending
#  s, squash = use commit, but meld into previous commit
#  f, fixup = like "squash", but discard this commit's log message
#  x, exec = run command (the rest of the line) using shell
# These lines can be re-ordered; they are executed from top to bottom.
# If you remove a line here THAT COMMIT WILL BE LOST.
# However, if you remove everything, the rebase will be aborted.
# Note that empty commits are commented out
```

修改那一行

```
修改前
pick aagffsd I am commit message4 sadfsal;fjas;fjf;lsakfjas;lfkjsflksjf;slkfjsad;lfkasf;skjfs;alfjsdfjsfljsdf;lksdjf;slfjsd;lfjsdflf;fk


修改后
r aagffsd I am commit message4 
```

 r, reword = use commit, but edit the commit message

保存退出，下个页面编辑该commit的message，一直保存即可







### 注意

##### **本地多次提交后，提交到gerrit会要求合并多次，可以在本地手动执行变基操作将多个提交合并为一个**

**1,查看提交历史，git log**

首先你要知道自己想合并的是哪几个提交，可以使用git log命令来查看提交历史，假如最近4条历史如下：

```
commit 3ca6ec340edc66df13423f36f52919dfa3......

commit 1b4056686d1b494a5c86757f9eaed844......

commit 53f244ac8730d33b353bee3b24210b07......

commit 3a4226b4a0b6fa68783b07f1cee7b688.......
```

历史记录是按照时间排序的，时间近的排在前面。

**2,git rebase**

想要合并1-3条，有两个方法

1.从HEAD版本开始往过去数3个版本

```
git rebase -i HEAD~3
```

2.指名要合并的版本之前的版本号

```
git rebase -i 3a4226b
```

请注意3a4226b这个版本是不参与合并的，可以把它当做一个坐标

**3,选取要合并的提交**

1.执行了rebase命令之后，会弹出一个窗口，头几行如下：

```
pick 3ca6ec3   '注释**********'

pick 1b40566   '注释*********'

pick 53f244a   '注释**********'
```

2.将pick改为squash或者s,之后保存并关闭文本编辑窗口即可。改完之后文本内容如下：

```
pick 3ca6ec3   '注释**********'

s 1b40566   '注释*********'

s 53f244a   '注释**********'
```

3.然后保存退出，Git会压缩提交历史，如果有冲突，需要修改，修改的时候要注意，保留最新的历史，不然我们的修改就丢弃了。修改以后要记得敲下面的命令：

```
git add .  

git rebase --continue  
```

如果你想放弃这次压缩的话，执行以下命令：

```
git rebase --abort  
```

4.如果没有冲突，或者冲突已经解决，则会出现如下的编辑窗口：

```
# This is a combination of 4 commits.  
#The first commit’s message is:  
注释......
# The 2nd commit’s message is:  
注释......
# The 3rd commit’s message is:  
注释......
# Please enter the commit message for your changes. Lines starting # with ‘#’ will be ignored, and an empty message aborts the commit.
```

5.输入wq保存并推出, 再次输入git log查看 commit 历史信息，你会发现这两个 commit 已经合并了

参考链接：https://segmentfault.com/a/1190000007748862