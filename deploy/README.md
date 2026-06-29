# 超天酱双机部署指南 v4.6

> 主力机 + 老电脑共享 Tunnel 87fc0324，Cloudflare 自动轮询。

---

## 架构

```
用户 → amechan.mote-pal.xyz → Cloudflare → Tunnel 87fc0324 ─┬─ 本地:8930 (主)
                                                             └─ 老电脑:8930 (备)
Cloudflare 自动轮询，关机后另一台独扛。
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
- 项目代码（通过 AnyDesk 传）
- `deploy\config-oldpc.yml` → 老电脑 `E:\amechan-daily\config.yml`
- `deploy\daemon_server.vbs` → 老电脑 `E:\amechan-daily\`
- `deploy\daemon_cloudflared.vbs` → 老电脑 `E:\amechan-daily\`

#### 2. 路由 DNS（只需执行一次，用主力机的 credentials 文件）
将主力机 `C:\Users\Haoze\.cloudflared\87fc0324-*.json` 复制到老电脑同路径，然后：
```powershell
cd E:\amechan-daily
.\cloudflared.exe tunnel route dns 87fc0324-d76a-4bdf-91a6-1873ae14bb7d amechan.mote-pal.xyz
```

#### 3. 启动
老电脑用 NSSM 管理服务：
```powershell
.\nssm.exe restart amechan-server
```

cloudflared 同理。

---

## 三、日常运维

| 操作 | 方式 |
|------|------|
| 更新代码 | AnyDesk 传文件 → `nssm restart amechan-server` |
| 传哪些文件 | `static/index.html`, `generator.py`, `prompts.py`, `server.py`, `config.py` |

---

## 四、cloudflared 本地管理模式

- `config.yml` + `cloudflared tunnel route dns` + `cloudflared tunnel --config config.yml run`
- 无需 Zero Trust Dashboard，无需信用卡
- DNS CNAME 指向 `UUID.cfargotunnel.com`
- 多台机器用同一 Tunnel UUID + 同一 credentials 文件 → CF 自动轮询
