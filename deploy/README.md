# 超天酱双机部署指南 v4.3

> 目标：本地主力机（主）+ 老电脑（备），前端 apiFetch 自动降级。

---

## 架构

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 → 本地:8930 (主)
                                           Tunnel 51cc70a8 → 老电脑:8930 (备)
       bak.mote-pal.xyz      → Cloudflare ─┘
前端 apiFetch 主失败 → 自动降级备用
```

---

## 一、本地主力机（这台电脑）

### 1. 首次路由 DNS（只需执行一次）
```powershell
cd C:\Users\Haoze
.\cloudflared.exe tunnel route dns 87fc0324-d76a-4bdf-91a6-1873ae14bb7d amechan.mote-pal.xyz
```

### 2. 启动 Server
```powershell
conda activate deepseek_v4_api
cd E:\Desktop\Deepseek_V4_API\amechan-daily
python server.py
```

### 3. 启动 Tunnel（另一个终端）
```powershell
cd C:\Users\Haoze\.cloudflared
..\cloudflared.exe tunnel --config config-local.yml run
```

---

## 二、老电脑（备用服务器）

### 首次部署步骤：

#### 1. 复制文件到老电脑
- 将 `deploy\config-oldpc.yml` 复制到老电脑 `E:\amechan-daily\config.yml`
- 将 `deploy\daemon_server.vbs` 复制到老电脑 `E:\amechan-daily\`
- 将 `deploy\daemon_cloudflared.vbs` 复制到老电脑 `E:\amechan-daily\`

#### 2. 路由 DNS（只需执行一次）
```powershell
cd E:\amechan-daily
.\cloudflared.exe tunnel route dns 51cc70a8-6e03-41b1-95f1-2d328dff6fdf bak.mote-pal.xyz
```

#### 3. 停掉旧的 remotely-managed tunnel
老电脑之前运行的是 `cloudflared tunnel run amechan`（Zero Trust 管理模式），需要停掉：
```powershell
# 关掉旧 tunnel 的 cmd 窗口，或 Ctrl+C
# 然后用新方式启动：
.\cloudflared.exe tunnel --config config.yml run
```

#### 4. 配置 Task Scheduler 开机自启（无需管理员）

**daemon_server 任务：**
1. 打开 `taskschd.msc`（任务计划程序）
2. 创建任务 → 名称: `amechan-server-daemon`
3. 常规 → 勾选 "仅在用户登录时运行"
4. 触发器 → 新建 → "登录时"
5. 操作 → 新建：
   - 程序: `wscript.exe`
   - 参数: `"E:\amechan-daily\daemon_server.vbs"`
6. 设置 → 勾选 "如果任务失败，每隔 1 分钟重启"

**daemon_cloudflared 任务：**
1. 同上，名称: `amechan-cloudflared-daemon`
2. 参数: `"E:\amechan-daily\daemon_cloudflared.vbs"`

#### 5. 确认 NSSM 服务已停用
如果之前用 NSSM 管理 server，现在由 daemon_server.vbs 接管，可以停掉 NSSM：
```powershell
.\nssm.exe stop amechan-server
.\nssm.exe remove amechan-server confirm
```

---

## 三、验证

### 检查主服务器
```powershell
curl https://amechan.mote-pal.xyz/api/stats
# 应返回 {"count": 0, "pool": 0, "status": "ok"}
```

### 检查备用服务器
```powershell
curl https://bak.mote-pal.xyz/api/stats
# 应返回 {"count": 0, "pool": 0, "status": "ok"}
```

### 检查前端 fallback
打开浏览器 F12 Console，访问 `https://amechan.mote-pal.xyz`。
如果主服务器宕机，应看到：`[api] 主力失联 → 降级老家`

---

## 四、日常运维

| 操作 | 命令 |
|------|------|
| 更新代码 | AnyDesk 传文件 → `nssm restart amechan-server`（如仍用NSSM） |
| 查看日志 | `E:\amechan-daily\daemon_server.log` |
| 手动重启 | 任务计划程序 → 右键任务 → 结束 → 运行 |

---

## 五、cloudflared 本地管理模式原理

- **Locally-managed**: `config.yml` + `cloudflared tunnel route dns` + `cloudflared tunnel --config config.yml run`
  - 无需 Zero Trust Dashboard
  - 无需信用卡
  - DNS CNAME 指向 `UUID.cfargotunnel.com`
  - 流量到达后由本地 config.yml 决定路由

- ~~Remotely-managed~~: `cloudflared tunnel run <name>`（已弃用）
  - 需要 Zero Trust Dashboard 管理 Public Hostname
  - 免费版需绑信用卡
