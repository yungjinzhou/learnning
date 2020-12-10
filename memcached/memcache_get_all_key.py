import memcache

mc = memcache.Client(['127.0.0.1:11211'], debug=True)
# mc.set("foo", "bar")
# value = mc.get("foo")
# print(value)  # 输出bar
keys_list = []
a=mc.get_stats("items")
mem_use=a[0][1].keys()
l_num=[]
# 这个for是从items找到类似于items:27:number 39 这样的值,最后l_num存储的是items:27:number 这个值
for n in mem_use:
    if n.endswith("number"):
        l_num.append(n)

for i in l_num:
    print(a[0][1])
    b=a[0][1][i]
    c=i.split(":")[1]
    d="cachedump" + " " + c +" " + b
    tmp_a=mc.get_stats(d)
#对某个slab中的所有keys获取keys值,对memcached所有keys进行get一次
    for n in tmp_a[0][1].keys():
         keys_list.append(mc.get(n))

print(keys_list)