# CjingDesignSystem
一个简易高校的策划表工具
####
基于Python实现读取excel表，并输出到Json文件中
同时支持将Json文件自动生成为C#的表类和读取代码

### Example
table:
| Id | WalkSpeed | RunSpeed |
| :-----| ----: | :----: |
| INT | FLOAT | FLOAT |
| 索引 | 走动速度 | 跑动速度 |
| 0 | 1.0f | 2.0f |
| 1 | 2.0f | 3.0f |

json:
```json
[
  {
    "Id": 0,
    "WalkSpeed": 1.0,
    "RunSpeed": 2.0
  },
  {
    "Id": 1,
    "WalkSpeed": 2.0,
    "RunSpeed": 3.0
  },
]
```

C#:
```c#
namespace Design
{
    public class PlayerTemplate : ITableGeneratorObject
    {
        public int Id { get; private set; }
        public float WalkSpeed { get; private set; }
        public float RunSpeed { get; private set; }
    }
}

void test()
{
    float walkSpeed = Design.DesignTables.Instance.Player.GetData(0).WalkSpeed
}
```



