# 数据源与检索路径

> **本文档全部 URL 通过 curl 实测可达性验证。**
> "实测状态"列含义：
> - `200` — 直接 HTTP 200，curl/网页读取 均可
> - `WAF` — 服务器返回 412/403 但内容真实存在，需用 网页读取 或浏览器 UA
> - `JS` — 静态 HTML 拉到但内容由 JS 渲染，需用 Search snippet 或换子域
> - `PDF` — 内容只在 PDF 中，需 curl 下载 + pypdf 解析
> - `404` — URL 已失效，已在第十节"失效域名修正表"中列出

## 一、数据可信度分级

| 级别 | 定义 | 可直接采用 |
|------|------|----------|
| A | 校招办官网（含 zsb / zs / zsc / zscx / admission / zhaoban / zhaosheng / bkzs / bzkzs / aoff / join 等子域）、省考试院（.gov.cn 域 / 各省考试院域，含投档线 PDF）、阳光高考 chsi.com.cn | 是 |
| B | 教育部直属机构、官方授权工具（掌上高考 gaokao.cn、中国教育在线 eol.cn / gaokao.eol.cn 引述官方部分） | 需 1 条 A 级或 2 条 B 级交叉 |
| C | 主流聚合站（高考 100、6617、新高考网 hfplg、555edu、自主选拔在线 zizzs、本地宝 bendibao、搜狗教育 转载页 等） | 必须 ≥ 2 条独立 C 站交叉验证；单 C 源 → 备选清单 |
| D | 商业宣传、第三方解读 | 不可用 |
| E | 模型记忆 / 估算 | 绝对禁止 |

**特别说明**：搜索引擎返回的 search snippet 若来自 A 级域名（校招办、省考试院），**snippet 本身就是 A 级源**，无需打开页面即可采用。

## 二、访问方式速查（必读）

不同数据源对工具有不同要求，下表是已验证的最佳访问方式：

| 源类型 | 推荐工具 | 备选 | 失败时降级 |
|-------|---------|------|----------|
| 省考试院主站（HTML） | 网页读取 | curl + UA 头 | 换搜狗教育 转载页 |
| **省考试院投档线 PDF** | curl 下载 + pypdf 解析 | — | 无替代，PDF 是最高 A 级源 |
| 阳光高考 chsi.com.cn | **网页读取**（curl 必 412） | — | 换中国教育在线转载 |
| 校招办主站 zsb.xxx.edu.cn | curl + UA → 看 200/412 | 网页读取 | 换 zs / zscx / admission 子域 |
| 校招办子域（admission/zscx 等） | curl 直拉，多数 200 | 网页读取 | 换搜狗教育 转载页 |
| 校招办章程页 | curl 直拉 | 联网检索 site: 拿 snippet | 中国教育在线 eol.cn 转载 |
| 搜狗教育 转载页 | curl + UA | 网页读取 | — |
| 本地宝 转载页 | curl + UA | 网页读取 | — |
| 中国教育在线 | 网页读取 | curl | — |

**curl 标准命令**（用于所有 .edu.cn 域）：

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
curl -sL -m 12 -A "$UA" "$url"
```

**关键反爬规则**：
- 阳光高考 chsi.com.cn 对 curl/任何 UA 都返回 412 → **必须用 网页读取**
- 北京邮电大学 zsb.bupt.edu.cn 对 curl 返回 412 → 用 网页读取 或换 zscx.bupt.edu.cn 子域
- 中山大学 admission.sysu.edu.cn HTTPS 对 curl 412 → 用 HTTP，或换 zs.sysu.edu.cn 子域
- 河南省考试院 haeea.cn 对默认 UA 412 → 加上面的浏览器 UA 头
- 域名 NXDOMAIN 时不要硬试，直接换正确域名（见第十节）

## 三、按数据类型组织的检索路径

### 一分一段表（A 级必查）

> **完整 31 省份考试院域名（已实测）见 `nationwide-coverage.md` 第二节**。下表是高频常用省份摘要：

| 省份 | 考试院官网 | 实测状态 | 访问方式 |
|------|----------|---------|---------|
| 北京 | https://www.bjeea.cn | 200 | 网页读取 / curl 直拉 |
| 江苏 | https://www.jseea.cn | 200 | curl 直拉 |
| 山东 | https://www.sdzk.cn | 200 | curl 直拉 |
| 浙江 | https://www.zjzs.net | 200 | curl 直拉 |
| 广东 | https://eea.gd.gov.cn | 200 | curl 直拉 |
| 湖北 | http://www.hbea.edu.cn | 200 | curl 直拉 |
| 四川 | https://www.sceea.cn | 200 | curl 直拉 |
| 河南 | http://www.haeea.cn | WAF（412） | curl + 浏览器 UA / 网页读取 |
| 辽宁 | http://www.lnzsks.com | 200 | curl 直拉 |
| 福建 | https://www.eeafj.cn | 200 | curl 直拉 |
| 安徽 | https://www.ahzsks.cn | 200 | curl 直拉 |
| 陕西 | http://www.sneea.cn | 200 | curl 直拉 |
| 河北 | http://www.hebeea.edu.cn | 200 | curl 直拉 |
| **吉林** | **https://www.jleea.com.cn** | 200 | curl（**新域名**，旧 .edu.cn 已 404） |
| **黑龙江** | **https://www.hljea.org.cn** | 200 | curl（**新域名**） |
| **贵州** | **https://zsksy.guizhou.gov.cn** | 200 | curl（gov.cn 域，旧 eaagz.org.cn 不可用） |
| **西藏** | **http://zsks.edu.xizang.gov.cn** | 200 | curl（gov.cn 域，旧 xzzsks.com.cn 不可用） |

**检索话术**：
```
[省份] [年份] 高考一分一段表 [科类]
[省份] [年份] 普通高考分段统计表 site:gov.cn
[省份] 一分一段 site:[省考试院域名]
```

**位次反推**：考试院 PDF 给"分数+累计人数"，考生分数对应位次 = 高于该分的累计人数 + 该分段人数 ÷ 2（取中位）。

### 院校层面投档线（A 级必查）

**最权威路径（必须优先）**：**省考试院发布的"普通批投档线" PDF**。

例如 北京：`https://www.bjeea.cn/uploads/soft/YYMMDD/178-XXX.pdf`，含全部院校专业组的官方投档分（含分数 + 位次），是当年录取数据的最高权威。

PDF 标准格式："序号 院校代码 院校名 专业组号 选科 总分 语文 数学 外语"。

**校招办历年分数页**（A 级，作为 PDF 之外的第二验证）。**全部已实测**：

| 院校 | 招办网址 | 实测 | 访问方式 |
|------|---------|------|---------|
| 清华大学 | https://www.join-tsinghua.edu.cn | 200 | curl |
| 北京大学 | https://admission.pku.edu.cn | 200 | curl |
| 中国人民大学 | https://rdzs.ruc.edu.cn | 200 | curl |
| 北京邮电大学（主站） | https://zsb.bupt.edu.cn | WAF（412） | 网页读取 / 用 zscx 子域 |
| 北京邮电大学（历年分数） | https://zscx.bupt.edu.cn/zsw/lnfs.html | 200 | curl 直拉 |
| 北京理工大学 | https://admission.bit.edu.cn | 200 | curl |
| 北京理工大学（历年分数） | https://admission.bit.edu.cn/static/front/bit/basic/html_web/lnfs.html | 200 | curl 直拉 |
| **北京航空航天大学** | **https://zs.buaa.edu.cn** | 200 | curl（注意非 zsb 子域） |
| 北京科技大学 | https://zhaosheng.ustb.edu.cn | 200 | curl |
| 北京交通大学 | https://zsw.bjtu.edu.cn | 200 | curl |
| 武汉大学 | https://aoff.whu.edu.cn | 200 | curl |
| 华中科技大学 | https://zsb.hust.edu.cn | 200（HTTPS） | curl，**禁用 HTTP** |
| 武汉理工大学 | https://zs.whut.edu.cn | 200 | curl |
| **中国地质大学(武汉)** | **https://zhaosheng.cug.edu.cn** | 200（部分网络 DNS 失败） | 网页读取 |
| 中山大学 | http://admission.sysu.edu.cn | 200（HTTP） | curl，HTTPS 会 WAF |
| 暨南大学 | https://zsb.jnu.edu.cn | 200 | curl |
| 深圳大学 | https://zs.szu.edu.cn | 200 | curl |
| 华南农业大学 | https://zsb.scau.edu.cn | 200 | curl |
| **四川大学** | **https://zs.scu.edu.cn** | WAF（412） | 网页读取 |
| 苏州大学 | https://zsb.suda.edu.cn | 200 | curl |
| **江南大学** | **https://admission.jiangnan.edu.cn** | 200 | curl |
| 河海大学 | https://zsw.hhu.edu.cn | 200 | curl |
| **南京邮电大学** | **https://zs.njupt.edu.cn** | 200 | curl |
| 中国矿业大学 | https://zs.cumt.edu.cn | 200 | curl |
| **重庆医科大学** | **https://bzkzs.cqmu.edu.cn** | 200 | curl（本专科招生新版）|
| **河南师范大学** | **https://www.htu.edu.cn/zs/** | 200 | curl |
| 信阳师范大学 | https://zs.xynu.edu.cn | 200 | curl |
| 川北医学院 | https://admission.nsmc.edu.cn | 200 | curl |
| 山东大学 | http://www.bkzs.sdu.edu.cn | 200 | curl |
| **中国海洋大学** | **https://bkzs.ouc.edu.cn** | 200 | curl（无 www）|
| 山东师范大学 | http://www.zsb.sdnu.edu.cn | 200 | curl |
| 东北财经大学 | https://zs.dufe.edu.cn | 200 | curl |

**已知失效或需要修正的域名以粗体标注**（详见第十节）。

### 招生代码精确性要求（必读）

新高考省份（北京、天津、上海、海南、山东、浙江）实行"院校专业组"模式，**同一所大学在同一省份会有多个独立招生代码**。例如：

- 北京邮电大学在京有 1028（普通类）、1029（中外合作）、1030（其他批次）三个代码
- 北京航空航天大学 1048-02、1048-03、1048-04 是三个独立专业组，分数差可达 30+

**报告中必须精确到"院校代码 + 专业组号"**（如"北邮 1028-02"），不能只写"北邮"。来源仅校招办章程或省考试院投档线 PDF，禁止凭印象写。

### 专业组明细（A 级必查；B/C 级需交叉）

**最佳路径**：校招办上述链接的"分专业录取情况"页或专属 PDF；**省考试院 PDF 中"专业组号"列即为权威值**。

**降级时**：聚合站（高考 100、6617、555edu）必须找 ≥ 2 个独立站点对同一年份同一专业组的数据，且数字一致。

### 招生章程 / 选科要求 / 单科门槛（A 级必查）

| 路径 | 网址 | 实测 | 访问方式 |
|------|------|------|---------|
| 阳光高考招生章程库 | https://gaokao.chsi.com.cn/zsgs/zhangcheng.do | WAF（412） | **必须用 网页读取**，curl 无效 |
| 校招办当年章程 | 第三节"院校层面投档线"表中的招办网址 → 招生章程栏目 | 见上表 | 见上表 |
| 中国教育在线章程转载 | https://www.eol.cn/m/gaokao | 200 | 网页读取 / curl 直拉 |

**禁止**：用模型记忆判断单科门槛、选科要求；这些每年都可能调整。

### 学费（A 级必查）

**唯一可靠路径**：**当年招生章程**中的"收费标准"或"学费"条款。

招生章程通常在 6 月初前发布。

**写法规则**：找到 → 写具体金额（如"5500 元/年"） + 引用招生章程链接；找不到 → 用第五节"模型主动核实手段"穷尽尝试，**不允许直接降级到"建议核实"**。

**典型偏差**：使用 C 级源时，中外合作学费可能偏离招生章程口径数千至上万元（实际口径以"x-y 万/年"区间公布而非单一数值），必须以招生章程为准。

### 保研率（A 级必查）

**唯一可靠路径**：

| 路径 | 说明 |
|------|------|
| 校就业指导中心 career.xxx.edu.cn | 每年 12 月底前后发布的"毕业生就业质量报告" |
| 学校年报 / 学校官网"学校概况" | 部分学校年报披露 |

**禁止**：用"业内估算 50%+"等模糊表述。

**写法规则**：找到 → 写"约 X%（来源：[年份] [校名] 毕业生就业质量报告，链接：...）"；找不到 → 写"建议查 [校就业网] 最新就业质量报告"。

### 大类分流规则 / 转专业政策（A 级必查）

**唯一可靠路径**：

1. 校招办当年招生章程（部分章程明示分流规则）
2. 校官网 → 教务处 / 培养方案
3. 校招办 FAQ / 答考生问

**禁止**：用"业内常见做法"写规则细节。

### 校区位置（A 级必查）

**路径**：校官网"院系设置 / 校区分布"页或当年招生章程"办学地点"条款。

**注意**：多校区培养差异（如山大济南/青岛/威海，哈工大本部/威海/深圳，电子科大沙河/清水河）必须在章程中核实"该专业组本科 4 年在哪个校区"。

### 体检受限（A 级必查）

| 路径 | 网址 | 实测 |
|------|------|------|
| 教育部 | https://www.moe.gov.cn | 200 |
| 校招办章程"体检要求" | 第三节表格 | 见上表 |

教育部《普通高等学校招生体检工作指导意见》是底线；部分校加严，需查章程。

## 四、检索话术模板

### 查询某高校在某省近年录取数据

```
[高校名] [年份] [省份] [文/理/物理类/历史类] 录取分数线 位次
[高校名] [年份] [省份] [科类] 投档线 最低位次
[高校名] 历年分数 site:[校招办域名]
[省份]教育考试院 [年份] 普通批 投档线 PDF site:[省考试院域名]
```

### 查询专业组录取数据（新高考省份）

```
[高校名] [年份] [省份] 院校专业组 录取最低分
[高校名] [院校代码] 专业组 [年份] [省份]
[高校名] 分专业录取情况 site:[校招办域名]
```

### 查询一分一段表

```
[省份] [年份] 高考一分一段表 [文/理/物理类/历史类]
[省份] [年份] 普通高考分段统计表 site:gov.cn
```

### 查询招生章程要点

```
[高校名] [年份] 招生章程 单科要求 体检要求 转专业政策
[高校名] [年份] 招生简章 学费 收费标准
```

### 查询保研率

```
[高校名] [年份] 毕业生就业质量报告 保研率 推免
[高校名] 推免比例 site:career.xxx.edu.cn
```

## 五、模型主动核实手段（不要轻易降级）

网页读取 拉招办官网失败时（"No readable content found"通常是 JS 动态页），按下列顺序穷尽尝试：

### 5.1 子域替换（NXDOMAIN/000 时第一步）

不同学校招办的子域命名各异，主站不通时按下列经验顺序试：

```
zsb → zs → zsc → zscx → admission → zhaoban → zhaosheng → bkzs → bzkzs → aoff → join
```

**遇 NXDOMAIN 不要硬试**——直接 联网检索 "[校名] 本科招生网 官网" 拿正确域名。第十节列了已知失效域名清单。

### 5.2 招办静态镜像

| 招办主站类型 | 静态镜像或子域 | 实测 |
|------------|--------------|------|
| zsb.xxx.edu.cn 主站（动态/JS 渲染） | zsc / zscx / admission / zhaoban / zhaosheng / bkzs 子域常为静态 | 见第三节 |
| 校招办章程 | 中国教育在线 https://www.eol.cn/m/gaokao | 200 |
| 校招办章程 | 阳光高考章程库 https://gaokao.chsi.com.cn/zsgs/zhangcheng.do | WAF，必用 网页读取 |
| 历年录取数据 | 搜狗教育 https://m.sogou.com/openapi/h5/university/scoreLine?school=校名 | 200 |
| 历年录取数据 | 本地宝 https://m.bj.bendibao.com/edu/gkfenshuxian/school.php?id=校码 | 200 |
| 省考试院投档线 | 直接 PDF：如 https://www.bjeea.cn/uploads/soft/YYMMDD/178-XXX.pdf | PDF |

### 5.3 PDF 直链解析（用 Python pypdf）

省考试院发布的"普通批投档线"经常是 PDF（**最权威 A 级源**）。处理方法：

```bash
# 1. 下载 PDF（招办 PDF 通常无 robots 限制，curl 即可）
curl -sLo /tmp/x.pdf "https://www.bjeea.cn/uploads/soft/.../xxx.pdf"

# 2. 用 Python pypdf 提取文本（系统 Python 即可）
/usr/bin/python3 -c "
from pypdf import PdfReader
reader = PdfReader('/tmp/x.pdf')
text = '\n'.join(p.extract_text() for p in reader.pages)
print(text)
" | grep '北京邮电'
```

PDF 标准格式："序号 院校代码 院校名 专业组号 选科 总分 语文 数学 外语"。

**46 页 PDF 约 64K 字符，完全可一次性读入**。如系统未装 pypdf：`/usr/bin/pip3 install --user pypdf`。

### 5.4 Search snippet 即 A 级源

校招办主站搜索摘要里经常直接显示"计算机类(元班)671 电子信息类(元班)668..." 等数据。**Search 摘要本身就是 A 级源**——它来自校招办首页静态 HTML，无需 fetch 就能拿到。

```
site:zsb.xxx.edu.cn [年份] [省份] 投档线
site:eol.cn [校名] [年份] 招生章程
```

### 5.5 招生计划与学费

`m.sogou.com/openapi/h5/university/admission?school=...` 经常完整 转载页 校招办的招生计划表，含每个专业的学费。用 search snippet 即可拿到。

### 5.6 升级判定规则

经过上述 5 类手段拿到的数据，按下列规则升级到 A/B 级：

- 校招办子域返回的章程原文：**A 级**
- 省考试院 PDF 解析结果：**A 级**（且优先级高于校招办）
- 中国教育在线 / 阳光高考 引述章程：**B 级**（与 A 级一致即可采用）
- 搜狗教育 / 本地宝 转载页 自校招办：**B 级**（与另一 B/C 级交叉一致即可采用）

## 六、检索质量控制

1. **时间过滤**：优先用最近 1 年内发布的页面，警惕 2022 年以前的旧数据
2. **来源核验**：陌生网站的数据要在阳光高考或考试院再确认一次
3. **差异处理**：不同来源数据有出入时，**以省考试院 PDF / 校招办为准**；记录差异并在报告中注明
4. **缺失处理**：检索不到 3 年完整数据时，至少要有 N-1 年；如只有 N 年或全无，移入备选清单
5. **专业组细分**：同一所学校不同专业组的录取分数差异可能高达 30 分，必须查到专业组级别数据才算合格
6. **A 级源覆盖率**：主推清单的每所校，**录取分数+学费+选科要求三项中至少 2 项必须有 A 级源**

## 七、引用格式

报告中所有数据必须标注来源，格式如下：

```
[1] 北京邮电大学 2025 年北京市投档线（专业组 02 计算机类元班 671 分），
    来源：北京教育考试院 2025 年普通批投档线 PDF，
    https://www.bjeea.cn/uploads/soft/.../xxx.pdf
[2] 北京市 2025 年综合改革一分一段表，来源：北京教育考试院，
    https://www.bjeea.cn/xxx
```

**位次反推必须显式标注**：

```
[3] 北京邮电大学 2024 年北京市计算机类元班最低分 663（来源：北邮招办 https://...）；
    位次约 1800（基于北京 2024 年综合改革一分一段表反推，非招办直接公布）
```

## 八、当数据不可获取时的处理

仅当上述所有手段（招办主站 / 招办静态子域 / 中国教育在线 / 阳光高考 / 搜狗教育 转载页 / 本地宝 转载页 / PDF 直链解析）**全部失败**后，才允许在报告中标"建议家长在 [指定网址] 核实"，并在脚注中列出已尝试过的检索路径，让家长能复现核实步骤。

- **不要编造**
- **不要用模型记忆代替**
- 如该校属于"冲"档，可保留并加风险提示；如属于"稳"或"保"档，建议从清单移除以免误导
- **保研率、学费、大类分流规则、转专业政策**这四类信息中：
  - **学费、大类分流规则、转专业政策** 通常都能从招生章程拉到（用第五节的方法），不允许轻易标"建议核实"
  - **保研率** 大多数情况只能在校就业网年度报告中找，找不到时才允许标"建议核实"

## 九、各省考试院投档线 PDF 直链规律

各省考试院发布投档线 PDF 的路径有规律，可直接构造：

| 省份 | PDF 路径模式 | 范例 |
|------|------------|------|
| 北京 | `https://www.bjeea.cn/uploads/soft/YYMMDD/178-NNN.pdf` | bjeea.cn/uploads/soft/250720/178-XXX.pdf |
| 山东 | `https://www.sdzk.cn/`"普通类常规批投档情况" | 跳到通知公告搜索"投档" |
| 江苏 | `https://www.jseea.cn/`"普通类本科平行志愿投档线" | 跳到考试招生→普通高校招生 |
| 浙江 | `https://www.zjzs.net/`"普通类一段平行投档分数线" | 跳到信息发布 |
| 广东 | `https://eea.gd.gov.cn/`"普通类（物理/历史）投档情况" | 跳到信息查询 |

**通用路径**：`site:[省考试院域名] [年份] 投档线 filetype:pdf` 即可拿到 PDF 直链。

## 十、失效域名修正表（必读）

下列域名经实测不存在或不可用，**禁止再使用**。本表用于维护时的回归检查：

| 错误 URL | 正确 URL | 错误类型 |
|-----------|---------|---------|
| `https://zhaoban.cug.edu.cn` | `https://zhaosheng.cug.edu.cn` | NXDOMAIN |
| `https://zsb.scu.edu.cn` | `https://zs.scu.edu.cn` | NXDOMAIN |
| `https://zs.jiangnan.edu.cn` | `https://admission.jiangnan.edu.cn` | NXDOMAIN |
| `https://zsb.njupt.edu.cn` | `https://zs.njupt.edu.cn` | NXDOMAIN |
| `https://zs.cqmu.edu.cn` | `https://bzkzs.cqmu.edu.cn` | NXDOMAIN |
| `https://zsb.htu.edu.cn` | `https://www.htu.edu.cn/zs/` | NXDOMAIN |
| `http://zsb.buaa.edu.cn` | `https://zs.buaa.edu.cn` | NXDOMAIN |
| `https://www.bkzs.ouc.edu.cn` | `https://bkzs.ouc.edu.cn` | 多余 www |
| `http://zsb.hust.edu.cn` | `https://zsb.hust.edu.cn` | HTTP→502 |
| `https://admission.sysu.edu.cn` | `http://admission.sysu.edu.cn` | HTTPS WAF |

## 十一、典型偏差模式速查

下列偏差均为"依赖单 C 源、未走第五节穷尽核实"的固有产物。每条都给出"必须改用的 A 级路径"以供反查：

| 偏差类型 | 偏差幅度 | 根因 | 必须改用的 A 级路径 |
|---------|---------|------|------|
| 同一专业组分数偏差 | 4-8 分 | 单 C 源未与省考试院 PDF 对照 | 省考试院投档线 PDF（第五节路径 1） |
| 不同专业组分数串号 | 10-15 分 | C 源把同校不同专业组数据混淆 | 省考试院投档线 PDF + 校招办专业组明细 |
| 中外合作学费 | 偏差 20%+ | 用模型记忆代替章程原文 | 校招办当年招生章程"收费标准" |
| 漏掉同校多招生代码 | 漏 1-3 个 | 未读省考试院投档线 PDF（新高考省份普遍多代码） | 省考试院投档线 PDF |
| 招办子域 NXDOMAIN | URL 不可达 | 凭命名猜测未实测 | 走第十节"失效域名修正表"或子域穷举 |

**结论**：模型记忆 + 单 C 源 + 未实测 URL = 错误率 30%+；省考试院 PDF + 校招办子域 + curl 实测 = 错误率近 0。**永远先实测，永远先走 A 级源。**

## 十二、维护规约

本文档每 6 个月做一次回归测试：

```bash
# 跑下列脚本，发现 != 200 的逐一替换
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
for url in <从本文档抓所有 https?:// URL>; do
  echo "$(curl -sLo /dev/null -w '%{http_code}' -m 12 -A "$UA" "$url")  $url"
done
```

新发现的 NXDOMAIN/失效域名追加到第十节"失效域名修正表"，并更新对应章节。
