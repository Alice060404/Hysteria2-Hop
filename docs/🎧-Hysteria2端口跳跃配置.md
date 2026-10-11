# 🎧 3X-UI Hysteria2 端口跳跃配置教程

适用：Ubuntu 24.04、3X-UI、Hysteria2。项目：[Hysteria2-Hop](https://github.com/hcloudlab/Hysteria2-Hop)。

## 一、3X-UI 入站配置

打开 **3X-UI → 入站列表 → 添加/修改 Hysteria2 入站**。

### 基础配置

| 配置项 | 本次实测值 |
| --- | --- |
| 协议 | Hysteria |
| 监听地址 | 留空（监听所有 IP） |
| 监听端口 | `443` |

### 传输配置

| 配置项 | 本次实测值 |
| --- | --- |
| UDP 空闲超时 | 60 秒 |
| 伪装 | 开启 |
| 伪装类型 | default (404 page) |
| Sockopt | 关闭 |
| UDP Masks | 添加 UDP Mask 1 |
| UDP Mask Type | Salamander (Hysteria2) |
| Mode | Salamander |
| Salamander Password | 自行生成，客户端保持一致 |
| QUIC Params | 开启 |
| Congestion | BBR |
| BBR Profile | standard |
| Debug | 关闭 |
| UDP Hop | **开启** |
| Hop Ports | **`20000-30000`** |
| Hop Interval | **30 秒** |
| Max Idle Timeout | 30 秒 |
| Keep Alive Period | 10 秒 |
| Disable Path MTU Discovery | 开启（本次实测设置） |
| Disable Chrome Parrot | 关闭 |
| Disable GSO | 关闭 |
| Disable Stateless Reset | 关闭 |
| Max Incoming Streams | 1024 |
| Init Stream Window | 8388608 |
| Max Stream Window | 8388608 |
| Init Conn Window | 20971520 |
| Max Conn Window | 20971520 |

Hop Ports 可自行调整，但**不能包含实际监听端口**。Disable Path MTU Discovery 的设置来自本次链路测试，不是所有网络环境的强制要求。

### 安全配置

| 配置项 | 本次实测值 |
| --- | --- |
| 安全 | TLS |
| SNI | 与实际证书匹配（本次使用 VPS IP） |
| TLS 最小 / 最大版本 | 1.2 / 1.3 |
| ALPN | `h3` |
| 拒绝未知 SNI | 关闭 |
| 禁用系统根 | 关闭 |
| 会话恢复 | 关闭 |
| 数字证书 | 文件路径 |

本次实测证书路径（**仅示例，按实际证书修改**）：

```text
证书：/root/cert/ip/fullchain.pem
私钥：/root/cert/ip/privkey.pem
```

其他未列出的选项保持默认。配置完成后点击 **保存更改**。

## 二、安装 Hysteria2-Hop

SSH 登录 VPS，执行：

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/hcloudlab/Hysteria2-Hop/main/bootstrap.sh)"
```

脚本只读 3X-UI 数据库，根据入站的 Hop Ports 配置 nftables UDP 转发、UFW 规则和 systemd 启动恢复。**云厂商安全组需要另行放行 UDP 443 与所选跳跃端口范围。**

## 三、Shadowrocket 配置

| 配置项 | 内容 |
| --- | --- |
| 类型 | Hysteria2 |
| 地址 | VPS 公网 IP |
| 端口 | `20000-30000` |
| 认证密码 | 与 3X-UI 的 Hysteria2 用户密码一致 |
| Salamander 混淆密码 | 与 UDP Mask Password 一致 |
| SNI / TLS | 与服务端证书设置一致 |

保存后连接测试。客户端端口范围须与服务端一致。

## 四、脚本常用命令

**查看配置状态：**

```bash
sudo /usr/local/sbin/hcloudlab-hy2hop status
```

显示 `STATUS: PASS` 仅代表本机规则检查通过，仍需客户端联网验证。

**在 3X-UI 修改 Hop Ports 并保存后更新规则：**

```bash
sudo /usr/local/sbin/hcloudlab-hy2hop update
```

有多个符合条件的入站时，指定实际入站 ID（`5` 为示例）：

```bash
sudo /usr/local/sbin/hcloudlab-hy2hop update --inbound-id 5
```

更新后记得同步修改客户端端口范围。

**查看 NAT / UFW：**

```bash
sudo nft list table ip hcloudlab_hy2hop
sudo ufw status
```

**查看开机自启与服务运行状态：**

```bash
systemctl is-enabled hcloudlab-hy2hop.service
systemctl is-active hcloudlab-hy2hop.service
```

正常启动后分别显示 `enabled`、`active`。

**查看支持的命令：**

```bash
sudo /usr/local/sbin/hcloudlab-hy2hop --help
```

**撤销脚本管理的配置：**

```bash
sudo /usr/local/sbin/hcloudlab-hy2hop restore
```

执行 restore 前确认不再需要端口跳跃功能。

[返回 README](../README.md)
