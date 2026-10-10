# HCloudLab · 3X-UI Hysteria2 UDP Hop V1 — Ubuntu 24.04

## 适用范围

- 3X-UI 面板中的 Hysteria2 入站：数据库 `protocol=hysteria`
- 在面板填写 **Hop Ports**，例如 `20000-30000`；脚本只读数据库，不修改 x-ui.db。
- 只支持 Ubuntu 24.04 + systemd；IPv4，存在全局 IPv6 地址时也创建 IPv6 规则。
- UFW 开启时自动添加跳跃范围的 UDP 放行规则；nftables 未安装时从 Ubuntu 软件源自动安装。
- 本版本不保证与 Docker 或其他自定义 NAT 规则共存；检测到其他 DNAT/redirect 将安全拒绝安装。

## 一键安装

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/hcloudlab/Hysteria2-Hop/main/bootstrap.sh)"
```

`bootstrap.sh` 只下载 `hy2hop.py` 本身（单文件，无其他依赖），编译检查后立即运行，不会在系统上留下安装脚本本身。安装后执行 `/usr/local/sbin/hcloudlab-hy2hop` 可再次打开菜单。

本地已有完整仓库时，也可以直接在仓库目录执行 `sudo bash install.sh`。

## 验收

1. 首次安装：检查是否自动安装 nftables，读取 Hop Ports 并生成 IPv4/IPv6 映射。
2. `sudo /usr/local/sbin/hcloudlab-hy2hop status`：检查当前配置。
3. 更新客户端订阅，真实连接并确认跳跃端口的 UDP 流量计数增加。
4. 连续执行 `update` 3 次，确保没有重复规则。
5. 重启 VPS，再执行 `status`，验证客户端仍可连接。
6. 在 3X-UI 修改 Hop Ports，再执行 `update`，检查旧范围消失、新范围可用。
7. 执行 `restore`，确认原 443/UDP 节点可用、其他防火墙规则不变。
8. 出现错误立即停止并提供完整终端输出；不要手工执行 `nft flush ruleset` 或关闭 UFW。

## 内部验证范围

- Python 语法检查与 18 项 mock/SQLite 自动化测试通过。
- 在隔离的 Ubuntu 24.04 容器中，用真实 `ss`/`nft`/`ufw`/`apt-get` 命令（非 mock）端到端跑通了完整的
  `install → status → update ×3（确认幂等、规则不重复）→ restore` 流程，并单独确认：
  - `apt-get install nftables` 在全新安装时不会自动启用/启动 `nftables.service`；
  - `ufw`/`nft -a list ruleset` 的真实输出格式与代码里的字符串匹配、正则解析完全一致；
  - 存在其他 DNAT/redirect 规则时能正确检测并拒绝安装，自身规则不会被误判为冲突。
- **尚未在 DMIT 真实 VPS、真实 3X-UI、真实 systemd 重启、真实 IPv6 全局地址环境中执行，也没有真实客户端连接验证。** `status PASS` 不是客户端连接成功的证明。
- 跨 nftables/UFW/systemd 的自动回滚实现了尽力清理；断电、SIGKILL、外部系统同时修改规则等情况下，不能保证严格事务原子性。
- 恢复不卸载 nftables 软件包，不修改 3X-UI 数据库。

## GitHub 发布入口

正式仓库：https://github.com/hcloudlab/Hysteria2-Hop

项目包含 `bootstrap.sh`（从 GitHub 获取核心脚本运行）与 `install.sh`（本地仓库直接启动）。不要将本地/容器内的自动化测试 PASS 当作面向真实用户的 Release Gate；DMIT 真实环境验收前仍需按"验收"一节逐项人工确认。
