# Vibecoding 代码审查 Checklist

本文档是主 SKILL.md 阶段 B 的深入补充。审查代码时按这四个维度过一遍。

## 维度 1：需求覆盖（Requirement Coverage）

### 核心问题
"代码真的实现了 PRD 要求的事吗？"——不是"代码能跑吗"。

### 审查方法
对照阶段 A 生成的用例表（特别是 P0 用例）和 PRD 的验收标准，逐条定位实现位置。

### 常见坑

**静默丢失需求**
- PRD 要求"密码错 5 次锁定"，代码只实现了"密码错了返回 401"
- PRD 要求"发送邮件确认"，代码调用了发送函数但没处理失败
- PRD 要求"记录操作日志"，代码里没找到任何日志调用

**只实现 happy path**
- [某验证功能]只有"验证成功"分支，没有"过期"、"错误次数过多"
- 分页接口只有第一页，边界情况（空、最后一页、翻页超过总数）没处理

**理解偏差**
- PRD 说"24 小时内不能重复发送"，代码实现成了"24 小时内只能发送一次"（是零次还是一次？）
- PRD 说"金额精确到分"，代码用了 float 而不是 Decimal

**伪实现**
- 函数存在但返回 mock/hardcoded 数据
- 有 if-else 分支但两个分支做的事一样
- catch 住异常但只 log 一下，业务逻辑没 fallback

### 输出形式
对每条验收标准打标签：
- ✅ 已实现（给出文件:行号证据）
- ⚠️ 部分实现（说明缺了什么）
- ❌ 未实现
- ❓ 找不到对应代码（可能在别的文件，需要用户补充上下文）

---

## 维度 2：代码质量（Code Quality）

### 2.1 空值处理

**常见坑：**
```python
# ❌ 直接访问可能为 None 的属性
user = db.get_user(user_id)
return user.name  # user 可能是 None

# ❌ 以为字典一定有某个 key
config = load_config()
port = config['port']  # 可能 KeyError

# ❌ JS 中对可选字段直接链式
const city = data.user.address.city  // 任一层为 null 就爆
```

**检查清单：**
- [ ] 数据库查询、API 响应、字典访问后有 None/null 检查？
- [ ] Optional 类型在使用前有解包/判空？
- [ ] JavaScript 中可选链 `?.` 或显式判空？
- [ ] 函数参数是否标注了允许 None 的情况？

### 2.2 边界条件

**常见坑：**
```python
# ❌ 空列表处理
def first_item(items):
    return items[0]  # 空列表时 IndexError

# ❌ 除零
def avg(nums):
    return sum(nums) / len(nums)  # 空列表时 ZeroDivisionError

# ❌ 字符串操作
def get_ext(filename):
    return filename.split('.')[1]  # 没有点时 IndexError
```

**检查清单：**
- [ ] 集合/数组操作前检查空？
- [ ] 除法操作前检查除数非零？
- [ ] 索引访问前检查范围？
- [ ] 循环有明确的终止条件？
- [ ] 递归有基线条件和深度保护？

### 2.3 异常处理

**常见坑：**
```python
# ❌ 吞掉所有异常
try:
    do_something()
except:
    pass  # 任何问题都无声消失

# ❌ 用异常控制正常流程
try:
    user = users[key]
except KeyError:
    user = create_user()  # 这应该是 if 不是 try

# ❌ catch 范围过宽
try:
    # 200 行代码
    ...
except Exception as e:
    log(e)  # 谁知道实际是啥错
```

**检查清单：**
- [ ] except/catch 捕获的异常类型是具体的，不是 bare `except:` 或 `catch(Exception)`？
- [ ] catch 后有合理的处理（重试/降级/友好提示），不是 `pass`、`log` 就完事？
- [ ] try 块不过大（不是包着半个函数）？
- [ ] 关键错误有 log，但错误 log 不泄漏敏感信息？

### 2.4 资源管理

**常见坑：**
```python
# ❌ 文件不关闭
f = open(path)
data = f.read()  # 忘了 close，或中间 raise 了

# ❌ 连接不释放
conn = db.connect()
do_query(conn)  # 如果 raise，conn 一直占着

# ❌ 锁不释放
lock.acquire()
# do stuff - 如果 raise，lock 永远持有
lock.release()
```

**检查清单：**
- [ ] 文件、连接、锁、信号量用 `with`/`try-finally` 管理？
- [ ] 多资源嵌套时考虑了反向释放顺序？
- [ ] Go 代码用了 `defer`？Rust 代码用了 RAII？

### 2.5 类型安全

**常见坑：**
```javascript
// ❌ == vs ===
if (x == 0) {...}  // '0', '', false, null 都会匹配

// ❌ 隐式转换
const total = items.reduce((a, b) => a + b.price, 0);
// 如果 b.price 是字符串，变成字符串拼接
```

```python
# ❌ Python 3 字节/字符串混用
data = response.content  # bytes
if data == 'ok':  # 永远 False
    ...

# ❌ isinstance 检查漏了子类
if type(x) == list:  # False if x 是 tuple
    ...
```

**检查清单：**
- [ ] JS 用 `===`/`!==`？
- [ ] Python 中 bytes 和 str 边界清楚？
- [ ] TypeScript 有没有大量 `any`？
- [ ] 数值类型转换明确（int/float/Decimal）？

---

## 维度 3：安全（Security）

### 3.1 注入攻击

**SQL 注入：**
```python
# ❌ 字符串拼接
cursor.execute(f"SELECT * FROM users WHERE name='{username}'")

# ❌ format/% 格式化
cursor.execute("SELECT * FROM users WHERE name='%s'" % username)

# ✅ 参数化查询
cursor.execute("SELECT * FROM users WHERE name=%s", (username,))
```

**命令注入：**
```python
# ❌ shell=True 拼接
os.system(f"convert {filename} out.png")
subprocess.run(f"grep {pattern} file.txt", shell=True)

# ✅ 参数列表 + 不用 shell
subprocess.run(["convert", filename, "out.png"])
```

**XSS（前端）：**
```javascript
// ❌ innerHTML 拼接用户输入
element.innerHTML = `<p>Hello ${userName}</p>`;

// ❌ React dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{__html: userContent}} />

// ✅ textContent 或 React 默认转义
element.textContent = userName;
```

**检查清单：**
- [ ] 所有 SQL 查询都用参数化，没有字符串拼接？
- [ ] 所有 shell 命令调用都避免 `shell=True`？
- [ ] 所有 HTML 输出都经过转义，或使用安全的模板引擎？
- [ ] 文件路径拼接防了 `../` 穿越？

### 3.2 鉴权与授权

**检查清单：**
- [ ] 每个需要登录的接口都有鉴权中间件/装饰器？
- [ ] 访问他人资源时检查了 owner？（防水平越权）
- [ ] 管理员接口有角色检查？（防垂直越权）
- [ ] Session/Token 过期处理正确？
- [ ] Token 刷新机制安全（refresh token 一次性）？
- [ ] 敏感操作有二次确认/[安全校验机制]？

### 3.3 敏感信息

**常见坑：**
```python
# ❌ 硬编码密钥
API_KEY = "sk-abc123def456..."
DB_PASSWORD = "admin123"

# ❌ 日志泄漏
logger.info(f"Login attempt: user={username}, pass={password}")

# ❌ 错误信息过详细
return jsonify({"error": f"DB query failed: {str(e)}"})  # 暴露 SQL 结构
```

**检查清单：**
- [ ] API key、密码、token 不硬编码在代码里？（用环境变量或 secrets manager）
- [ ] 日志中不包含密码、token、完整身份证号、完整银行卡号？
- [ ] 错误响应不泄漏内部实现（堆栈、SQL、文件路径）？
- [ ] Git 历史中没有 commit 过密钥？（`.env` 在 `.gitignore`？）

### 3.4 密码与加密

**常见坑：**
```python
# ❌ 用 md5/sha1 存密码
hashlib.md5(password.encode()).hexdigest()

# ❌ 用 random 生成 token
token = str(random.randint(10**15, 10**16))

# ❌ 自己实现加密
def encrypt(data, key):
    return ''.join(chr(ord(c) ^ ord(key[i%len(key)])) for i, c in enumerate(data))
```

**检查清单：**
- [ ] 密码用 bcrypt/argon2/scrypt 等慢哈希？
- [ ] 生成安全 token 用 `secrets.token_urlsafe()` / `crypto.randomBytes()`，不用 `random`？
- [ ] 不自己实现加密算法，用 AES、RSA 等标准库？
- [ ] 传输敏感数据用 HTTPS，不用明文 HTTP？

### 3.5 反序列化与执行

**常见坑：**
```python
# ❌ pickle 反序列化不可信数据
data = pickle.loads(user_upload)

# ❌ eval/exec 用户输入
result = eval(user_expression)

# ❌ yaml.load 不安全模式
config = yaml.load(user_yaml)  # 应该用 safe_load
```

**检查清单：**
- [ ] pickle 只用于可信来源？
- [ ] 不用 eval/exec 处理用户输入？
- [ ] yaml 用 `safe_load`？
- [ ] JSON 解析后对结构做了校验？

---

## 维度 4：性能与并发

### 4.1 数据库性能

**N+1 查询：**
```python
# ❌ 循环中查询
users = User.objects.all()
for user in users:
    orders = Order.objects.filter(user_id=user.id)  # N 次查询
    ...

# ✅ 一次 join / prefetch
users = User.objects.prefetch_related('orders')
```

**检查清单：**
- [ ] 循环内没有数据库查询？
- [ ] 没有用 `SELECT *` 查询大表？
- [ ] 大表查询有合适的索引（至少 WHERE 条件列上）？
- [ ] 分页使用了 LIMIT，没有一次返回全部？
- [ ] 大数据量导出用流式/分批，不是一次读内存？

### 4.2 并发问题

**竞态条件：**
```python
# ❌ check-then-act 不原子
if balance >= amount:
    balance -= amount  # 并发时可能超扣

# ✅ 用锁 或 原子操作 或 数据库事务
with lock:
    if balance >= amount:
        balance -= amount
```

**检查清单：**
- [ ] 共享状态的读写有锁/事务/原子操作？
- [ ] 锁的作用域尽可能小？
- [ ] 有死锁风险的场景分析过锁的获取顺序？
- [ ] [关键数据变更场景]（如数量、余额、计数器）用了数据库级别的锁或 CAS？
- [ ] 接口设计成幂等的（重复调用结果相同）？

### 4.3 阻塞与异步

**常见坑：**
```python
# ❌ async 函数里用阻塞调用
async def fetch_user(id):
    response = requests.get(url)  # 阻塞整个事件循环！
    return response.json()

# ✅ 用 aiohttp/httpx
async def fetch_user(id):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()
```

**检查清单：**
- [ ] async/await 函数里没有同步 I/O？
- [ ] CPU 密集任务不在主线程/主事件循环？
- [ ] 长时间操作有超时设置？
- [ ] 前端不在主线程做大量计算（考虑 Web Worker）？

### 4.4 循环与算法

**检查清单：**
- [ ] 循环有明确退出条件（防死循环）？
- [ ] 嵌套循环时考虑了复杂度（O(n²) 在 n 大时可能爆炸）？
- [ ] 查找操作用哈希表而不是线性扫描（当数据量大）？
- [ ] 递归有深度限制（防栈溢出）？

### 4.5 缓存与资源

**检查清单：**
- [ ] 缓存 key 设计不会冲突（带上版本、用户维度）？
- [ ] 缓存有合理的 TTL（不会永远旧数据）？
- [ ] 缓存击穿/雪崩有防护（互斥锁/随机过期）？
- [ ] 定时任务、后台任务有 graceful shutdown？
- [ ] 内存中缓存有上限（防 OOM）？

---

## 审查报告写作要点

### 严重等级定义

- 🔴 **严重（Critical）**：可能导致数据丢失、安全漏洞、生产崩溃、大规模影响的用户。典型：SQL 注入、任意代码执行、鉴权绕过、数据损坏、死锁、核心功能不工作。
- 🟡 **一般（Major）**：功能缺陷、明显的性能问题、部分用户受影响。典型：某个边界场景没处理、某个非核心接口慢、日志泄漏但不涉密。
- 🟢 **建议（Minor）**：代码风格、小优化、潜在风险。典型：命名不清、注释缺失、潜在的小性能优化。

### 证据要求
每个问题必须给出具体证据，不能空口说"代码质量差"：
- 文件名 + 行号
- 代码片段（1-5 行）
- 问题的具体技术说明（为什么是问题）
- 具体修复建议（给出改法的代码或步骤）

### 避免
- 不说"建议优化"不说什么、怎么优化
- 不列出一堆低优问题让关键问题淹没
- 不对 AI 代码风格本身做批评（变量名、注释等），聚焦功能/安全/性能
