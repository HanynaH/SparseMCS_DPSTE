# dp.py 笔记

## 矩阵含义

**P：** ground_truth 
	   其中交通数据：行表示top 100-500的道路，列表示时间每一列为一个小时，一共四天共96列。

## 参数定义

- $$
  {e\_epsilon}:e^\epsilon
  $$

- 

 

## 主函数

```python
def main(argv)
	变量定义
    异常处理
    选择recoverMethod
    选择adjustmentModel
    选择obfuscation_style
```



## 函数解释

1. **read_sensing_matrix**

   np.loadtxt(fname, dtype=<class 'float'>, comments='#', delimiter=None, converters=None, skiprows=0, usecols=None, unpack=False, ndmin=0)

   - fname 要读取的文件、文件名、或生成器
   - dtype 数据类型，默认float
   - comments 注释
   - delimiter 分隔符，默认是空格
   - skiprows 跳过前几行读取，默认是0，必须是int整型
   - usecols 要读取哪些列，从0开始计算。默认读取所有列。
   - unpack 如果为True，将分列读取

2. ****

   **create_sample_weight**
   **line 73**
   $$
   \begin{align}
   \omega(r^*) &= \omega_0 + (1-\omega_0) \cdot \frac{\overline{u}_{max}-\overline{u}(r^*)}{\overline{u}_{max}-\overline{u}_{min}}\\
   &=\omega_0 + (1-\omega_0) \cdot (1-\frac{\overline{u}(r^*)-\overline{u}_{min}}{\overline{u}_{max}-\overline{u}_{min}})\\
   &=\omega_0 + (1-\omega_0)-(1-\omega_0)\cdot\frac{\overline{u}(r^*)-\overline{u}_{min}}{\overline{u}_{max}-\overline{u}_{min}}\\
   &=1-(1-\omega_0)\cdot\frac{\overline{u}(r^*)-\overline{u}_{min}}{\overline{u}_{max}-\overline{u}_{min}}
   \end{align}
   $$
   

   ****

