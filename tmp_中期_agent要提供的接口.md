
**代码分类功能**
- 输入：代码内容，代码路径
	- 暂时直接调用静态分析工具，如果能结合大模型的memory、state等内容分析也可以加上
		- 写一个最简单的覆盖基本情况的测试用例：有asm、attribute、intrinsics
			- 最简单是指：
				- 不定义复杂的宏让语法分析失败
				- 这个代码里的外部符号在下面的已判断了的情况里有
					- CrossArch-Analyzer/LLM/core/attributes.json
					- CrossArch-Analyzer/LLM/core/predef_macro.json
					- 内联汇编写一个正常的能通过编译的应该都可以
						- [Playground - Tree-sitter](https://tree-sitter.github.io/tree-sitter/7-playground.html)
						- 在这里面测试，下面的Tree里没有“ERROR”就行
					- intrinsics常见的应该都可以判断出来
						- 代码写函数名不要写太怪的，比如`__riscv_v`开头的这种，只写一个普通的函数名
- 输出：分析结果json


**代码分析功能**
- 输入：代码内容，代码路径，用户自然语言命令
	- 暂时直接拼接成prompt，直接返回大模型分析结果
- 输出：分析结果字符串


如果有时间可以设计一下简单的算法，不用实现，到时候中期PPT写上去先