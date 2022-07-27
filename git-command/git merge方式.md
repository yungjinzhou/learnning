

## github上三种merge的区别



### merge

直接merge后前后对比

把当前commit直接合并到目标分支



![origin_and_merge](.\origin_and_merge.png)



### squarsh and merge

通过squarsh后在merge与最初对比

Squash Merge其实很简单，它就是在merge分支的时候把分支上的所有commit合并为一个commit后再merge到目标分支。



![origin_and_squarsh&merge](.\origin_and_squarsh&merge.png)



### rebase and merge

通过rebase后在merge与最初对比

rebase就是在merge分支的时候把分支上的所有commit都merge到目标分支。



![origin_and_rebase&merge](.\origin_and_rebase&merge.png)







