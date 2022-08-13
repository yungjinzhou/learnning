# asyncio_learn


## 简单概念1

### 事件循环

- 事件循环是一种处理多并发量的有效方式。事件循环利用poller对象，使得程序员不用控制任务的添加、删除和事件的控制。事件循环使用回调方法来知道事件的发生。它是asyncio提供的「中央处理设备」，支持如下操作：

- 注册、执行和取消延迟调用（超时）

- 创建可用于多种类型的通信的服务端和客户端的Transports

- 启动进程以及相关的和外部通信程序的Transports

- 将耗时函数调用委托给一个线程池

- 单线程（进程）的架构也避免的多线程（进程）修改可变状态的锁的问题。

### 并发编程

- 基于asyncio的应用要求应用代码显示的处理上下文切换。  
  asyncio提供的框架以事件循环(event loop)为中心，程序开启一个无限的循环，程序会把一些函数注册到事件循环上。当满足事件发生的时候，调用相应的协程函数。

### future

- future对象的状态

	- Pending

	- Running

	- Done

	- Cancelled

	- 创建future的时候，task为pending，事件循环调用执行的时候当然就是running，调用完毕自然就是done，如果需要停止事件循环，就需要先把task取消，状态为cancel。

- future是一个数据结构，表示还未完成的工作结果。事件循环可以监视Future对象是否完成。从而允许应用的一部分等待另一部分完成一些工作。

### task

- task是Future的一个子类，它知道如何包装和管理一个协程的执行。任务所需的资源可用时，事件循环会调度任务允许，并生成一个结果，从而可以由其他协程消费。

### 协程函数

- 带有async标识的函数

- 示例代码

	- import asyncio  
	    
	  async def main():  
	      print("hello")  
	      await asyncio.sleep(1)  
	      print('world')  
	    
	  coro = main()

- 一般异步方法被称之为协程(Coroutine)

- 调用时返回值: coroutine对象

## asyncio的常用函数

### asyncio.run学习

- 运行async函数,函数入口

	- 代码

		- import asyncio  
		    
		  async def main():  
		      print("hello")  
		      await asyncio.sleep(1)  
		      print('world')  
		    
		  asyncio.run(main())

	- asyncio.run(coroutine_func)

		- 首先建立event loop

		- 把coroutine变成event loop里的task

		- event loop 运行里面的task

- 两个task，排队执行  
  await分析

	- 代码

		- import asyncio  
		  import time  
		    
		    
		  async def say_after(delay, what):  
		      await asyncio.sleep(delay)  
		      print(what)  
		    
		    
		  async def main():  
		      print(f"started at {time.strftime('%X')}")  
		      await say_after(1, 'hello')  
		      await say_after(2, 'world')  
		      print(f"finished at {time.strftime('%X')}")  
		    
		    
		  asyncio.run(main())

	- 把coroutine变成task，进而执行task的方法, await coroutine_func

		- await

			- 把coroutine 对象包装成task，并告知event loop

			- 告知event loop，task完成后才能继续向下运行

			- yield操作，告知event loop，让其task继续执行，该task自己处理中

			- 当event loop再次运行该task时，把coroutine的真正返回值返回

	- 代码运行流程  
	  asyncio.run(main())

		- 首先建立event loop

		- 把main作为task放到了event loop

		- event loop 开始寻找task,发现只有main，运行main

			- 首先print

			- 运行了say_after，得到了coroutine object

			- await 这个coroutine object，把coroutine object 变成了task，放到event loop里，同时告知event loop需要等待该task完成，把控制权交给event loop，现在loop里task(main/say_after)，main在等say_after，event loop让say_after运行

				- 运行了asyncio.sleep，得到了coroutine object

				- await 这个coroutine object，把coroutine object 变成了task，放到event loop里，同时告知event loop需要等待1s后该task完成，await把控制权交给event loop,现在event loop有三个task，main/say_after/sleep

				- sleep运行完成后，event loop 有两个task（main/say_after）

				- say_after继续运行，print

			- say_after运行完成后，把控制权交给event loop,，现在event loop只有一个task(main)，再把控制权交给main

			- main开始向下运行

			- await 这个coroutine object，把coroutine object 变成了task，放到event loop里，同时告知event loop需要等待该task完成，把控制权交给event loop，现在loop里task(main/say_after)，main在等say_after，event loop让say_after运行

				- 运行了asyncio.sleep，得到了coroutine object

				- await 这个coroutine object，把coroutine object 变成了task，放到event loop里，同时告知event loop需要等待1s后该task完成，await把控制权交给event loop,现在event loop有三个task，main/say_after/sleep

				- sleep运行完成后，event loop 有两个task（main/say_after）

				- say_after继续运行，print

			- 继续运行main函数，print

	- 直接await可能遇到的问题

		- 所有控制权的返回都是显式的

			- event loop从task拿回控制权是被动的

				- 当函数运行完毕会交回控制权

				- await会交回控制权

		- 如果其中的一个task死循环，event loop就会卡住

- 并发执行  
  creat_task使用

	- 代码

		- import asyncio  
		  import time  
		    
		    
		  async def say_after(delay, what):  
		      await asyncio.sleep(delay)  
		      print(what)  
		    
		    
		  async def main():  
		      task1 = asyncio.create_task(say_after(1, 'hello'))  
		      task2 = asyncio.create_task(say_after(2, 'world'))  
		        
		      print(f"started at {time.strftime('%X')}")  
		      await task1  
		      await task2  
		      print(f"finished at {time.strftime('%X')}")  
		    
		    
		  asyncio.run(main())

	- 代码运行流程

		- 首先建立event loop

		- 把main作为task放到了event loop

		- event loop 开始寻找task,发现只有main，运行main

			- create_task把say_after变成task1，并且注册到event loop中

			- main继续执行，create_task把say_after变成task2，并且注册到event loop中

			- await task1时，此时event loop里有三个task（main/task1/task2）

			- 当task1告知event loop需要等待1s才能完成，event loop发现还有个task2可以运行

			- event loop开始执行task2

			- task1先完成，返回task1返回值

			- task2完成，返回

			- main这个task继续运行，print

	- create task的作用是把coroutine变成task，并且注册到event loop中

	- 当await 后直接是task时

		- 告知event loop，等待task完成，把控制权交给event loop

		- 等控制权回来时候，返回需要的返回值 

- 获取返回值

	- 代码

		- import asyncio  
		  import time  
		    
		    
		  async def say_after(delay, what):  
		      await asyncio.sleep(delay)  
		      return f"{what}-{delay}"  
		    
		    
		  async def main():  
		      task1 = asyncio.create_task(say_after(1, 'hello'))  
		      task2 = asyncio.create_task(say_after(2, 'world'))  
		    
		      print(f"started at {time.strftime('%X')}")  
		      ret1 = await task1  
		      ret2 = await task2  
		      print(ret1)  
		      print(ret2)  
		      print(f"finished at {time.strftime('%X')}")  
		    
		    
		  asyncio.run(main())

	- 

- gather使用  
  多个task运行

	- asyncio.gather返回的是future对象，也是可以await的,还可以gather

	- gather函数主要作用  
	  可传参数（coroutine/task/future）

	- gather参数是task

		- 代码

			- import asyncio  
			  import time  
			    
			    
			  async def say_after(delay, what):  
			      await asyncio.sleep(delay)  
			      return f"{what}-{delay}"  
			    
			    
			  async def main():  
			      task1 = asyncio.create_task(say_after(1, 'hello'))  
			      task2 = asyncio.create_task(say_after(2, 'world'))  
			    
			      print(f"started at {time.strftime('%X')}")  
			      ret = await asyncio.gather(task1, task2)  
			      print(ret)  
			      print(f"finished at {time.strftime('%X')}")  
			    
			    
			  asyncio.run(main())

	- gather参数是coroutine

		- 代码

			- import asyncio  
			  import time  
			    
			    
			  async def say_after(delay, what):  
			      await asyncio.sleep(delay)  
			      return f"{what}-{delay}"  
			    
			    
			  async def main():  
			      print(f"started at {time.strftime('%X')}")  
			      ret = await asyncio.gather(  
			          say_after(1, 'hello'),  
			          say_after(2, 'world')  
			      )  
			      print(ret)  
			      print(f"finished at {time.strftime('%X')}")  
			    
			    
			  asyncio.run(main())

		- 参数是coroutine

			- 首先转换成task

			- 注册到event loop里

			- 返回future值

			- 当await future时，相当于告诉event loop，要等待future里的任务都完成才能继续，同时会把task的return值放到list里，然后返回

### asyncio.wait

- 代码示例

	- import asyncio  
	    
	    
	  async def num(n):  
	      try:  
	          await asyncio.sleep(n*0.1)  
	          return n  
	      except asyncio.CancelledError:  
	          print(f"数字{n}被取消")  
	          raise  
	    
	    
	  async def main():  
	      tasks = [num(i) for i in range(10)]  
	      complete, pending = await asyncio.wait(tasks, timeout=0.5)  
	      for i in complete:  
	          print("当前数字",i.result())  
	      if pending:  
	          print("取消未完成的任务")  
	          for p in pending:  
	              p.cancel()  
	    
	    
	  if __name__ == '__main__':  
	      loop = asyncio.get_event_loop()  
	      try:  
	          loop.run_until_complete(main())  
	      finally:  
	          loop.close()

- 特点

	- 处理不需要顺序的任务

	- wait可以暂停一个协程，直到后台操作完成。

	- wait第二个参数为一个超时值  
	  达到这个超时时间后，未完成的任务状态变为pending

	- set是无序的所以这也就是我们的任务不是顺序执行的原因。wait的返回值是一个元组，包括两个集合，分别表示已完成和未完成的任务。

### asyncio.run_until_complete

- 一般使用

	- loop = asyncio.get_event_loop()

	- loop.run_until_complete(main())

	- loop.close()

- run_until_complete的参数是一个futrue对象。当传入一个协程，其内部会自动封装成task，其中task是Future的子类。关于task和future后面会提到。

- future学习

	- future状态

		- 代码

			- import asyncio  
			    
			    
			  def foo(future, result):  
			      print(f"此时future的状态:{future}")  
			      print(f"设置future的结果:{result}")  
			      future.set_result(result)  
			      print(f"此时future的状态:{future}")  
			    
			    
			  if __name__ == '__main__':  
			      loop = asyncio.get_event_loop()  
			      try:  
			          all_done = asyncio.Future()  
			          loop.call_soon(foo, all_done, "Future is done!")  
			          print("进入事件循环")  
			          result = loop.run_until_complete(all_done)  
			          print("返回结果", result)  
			      finally:  
			          print("关闭事件循环")  
			          loop.close()  
			      print("获取future的结果", all_done.result())

		- 可以通过输出结果发现，调用set_result之后future对象的状态由pending变为finished，Future的实例all_done会保留提供给方法的结果，可以在后续使用。

	- future使用await

		- 代码

			- import asyncio  
			    
			    
			  def foo(future, result):  
			      print("设置结果到future", result)  
			      future.set_result(result)  
			    
			    
			  async def main(loop):  
			      all_done = asyncio.Future()  
			      print("调用函数获取future对象")  
			      loop.call_soon(foo, all_done, "the result")  
			    
			      result = await all_done  
			      print("获取future里的结果", result)  
			    
			    
			  if __name__ == '__main__':  
			      loop = asyncio.get_event_loop()  
			      try:  
			          loop.run_until_complete(main(loop))  
			      finally:  
			          loop.close()

	- Future回调

		- 代码

			- import asyncio  
			  import functools  
			    
			    
			  def callback(future, n):  
			      print('{}: future done: {}'.format(n, future.result()))  
			    
			    
			  async def register_callbacks(all_done):  
			      print('注册callback到future对象')  
			      all_done.add_done_callback(functools.partial(callback, n=1))  
			      all_done.add_done_callback(functools.partial(callback, n=2))  
			    
			    
			  async def main(all_done):  
			      await register_callbacks(all_done)  
			      print('设置future的结果')  
			      all_done.set_result('the result')  
			    
			  if __name__ == '__main__':  
			      loop = asyncio.get_event_loop()  
			      try:  
			          all_done = asyncio.Future()  
			          loop.run_until_complete(main(all_done))  
			      finally:  
			          loop.close()

		- 通过add_done_callback方法给funtrue任务添加回调函数，当funture执行完成的时候,就会调用回调函数。并通过参数future获取协程执行的结果。

- 创建task方法

	- loop.create_task将协程包装为任务

	- asyncio.ensure_future(coroutine)

	- asyncio.create_task（python3.7）

### asyncio.as_complate

- as_complete是一个生成器，会管理指定的一个任务列表，并生成他们的结果。每个协程结束运行时一次生成一个结果。与wait一样，as_complete不能保证顺序，不过执行其他动作之前没有必要等待所以后台操作完成。

- 代码

	- import asyncio  
	  import time  
	    
	    
	  async def foo(n):  
	      print('Waiting: ', n)  
	      await asyncio.sleep(n)  
	      return n  
	    
	    
	  async def main():  
	      coroutine1 = foo(1)  
	      coroutine2 = foo(2)  
	      coroutine3 = foo(4)  
	    
	      tasks = [  
	          asyncio.ensure_future(coroutine1),  
	          asyncio.ensure_future(coroutine2),  
	          asyncio.ensure_future(coroutine3)  
	      ]  
	      for task in asyncio.as_completed(tasks):  
	          result = await task  
	          print('Task ret: {}'.format(result))  
	    
	    
	  now = lambda : time.time()  
	  start = now()  
	    
	  loop = asyncio.get_event_loop()  
	  done = loop.run_until_complete(main())  
	  print(now() - start)

### asyncio.gather

- asyncio.gather返回的是future对象，也是可以await的,还可以gather

- gather函数主要作用  
  可传参数（coroutine/task/future）

- gather参数是task

	- 代码

		- import asyncio  
		  import time  
		    
		    
		  async def say_after(delay, what):  
		      await asyncio.sleep(delay)  
		      return f"{what}-{delay}"  
		    
		    
		  async def main():  
		      task1 = asyncio.create_task(say_after(1, 'hello'))  
		      task2 = asyncio.create_task(say_after(2, 'world'))  
		    
		      print(f"started at {time.strftime('%X')}")  
		      ret = await asyncio.gather(task1, task2)  
		      print(ret)  
		      print(f"finished at {time.strftime('%X')}")  
		    
		    
		  asyncio.run(main())

- gather参数是coroutine

	- 代码

		- import asyncio  
		  import time  
		    
		    
		  async def say_after(delay, what):  
		      await asyncio.sleep(delay)  
		      return f"{what}-{delay}"  
		    
		    
		  async def main():  
		      print(f"started at {time.strftime('%X')}")  
		      ret = await asyncio.gather(  
		          say_after(1, 'hello'),  
		          say_after(2, 'world')  
		      )  
		      print(ret)  
		      print(f"finished at {time.strftime('%X')}")  
		    
		    
		  asyncio.run(main())

	- 参数是coroutine

		- 首先转换成task

		- 注册到event loop里

		- 返回future值

		- 当await future时，相当于告诉event loop，要等待future里的任务都完成才能继续，同时会把task的return值放到list里，然后返回

## asyncio.future和concurrent.futrues.Future联合使用  
  协程+线程(不支持异步的模块：线程执行的是不能协程的函数)

### import time  
  import asyncio  
  import concurrent.futures  
    
    
  def func1():  
  #某个耗时操作  
      time.sleep(2)  
      return “SB"  
    
  async def main():  
      1oop = asyncio.get_running_1oop()  
      # 1. Run in the default loop's executor (默认ThreadPoolExecutor )  
      # 第一步:内部会先调用ThreadpoolExecutor 的submit方法去线程池中申请一个线程去执行func1函数， 并返回一个concurrent.futures.Future对象  
      # 第二步：调用asyncio.wrap_future将concurrent.future.Future对象包装为asyncio.Future对象，因为concurrent.futures.Future对象不支持await语法，所以需要包装为asycio.Future对象 才能使用。  
      fut = 1oop.run_in_executor(None, func1)  
      result = await fut  
      print('default thread pool'， result)  
      #2. RuN ina custom thread pool:  
      # with Concurrent.futures.ThreadPoolExecutor() as pool:  
          # result = awai loop.run_in_executor(pool, func1)  
          # print(' custom thread pool'，result)  
    
      # 3. Run inacustom process pool:  
      # with concurrent.futures.ProcesspoolExecutor() as pool:  
          # pool, func1)  
          # print('custom process pool', result)  
  asyncio.run(main())

## 异步上下文管理器

### 包含了__aenter__和 __aexit__函数

## 异步迭代器

### 包含了 __aiter__和 __anext__函数

