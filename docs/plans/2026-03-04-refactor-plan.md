# 2026-03-04 代码重构计划

## 目标
全面检查并重构校园二手书交易平台，统一代码风格和逻辑

---

## Phase 1: 代码质量检查

### 1.1 依赖检查
- [x] Flask-Migrate 已添加
- [ ] 检查 requirements.txt 完整性

### 1.2 路由检查
- [ ] 所有路由端点一致
- [ ] 检查是否有死链

### 1.3 模型检查
- [ ] User 模型完整性
- [ ] Book 模型完整性  
- [ ] Order 模型完整性
- [ ] Review 模型完整性

---

## Phase 2: 样式统一

### 2.1 页面样式检查
- [x] 首页 index.html ✅
- [x] 登录 login.html ✅
- [x] 注册 register.html ✅
- [x] 个人资料 profile.html ✅
- [x] 编辑资料 edit_profile.html ✅
- [x] 我的书籍 my_books.html ✅
- [x] 发布书籍 create.html ✅
- [x] 书籍详情 detail.html
- [x] 编辑书籍 edit.html ✅
- [x] 智能定价 pricing_calculator.html ✅
- [x] 我的订单 my_orders.html ✅
- [x] 订单详情 detail.html ✅
- [x] 订单确认 create.html ✅
- [x] 评价 review.html ✅
- [x] 关于 about.html ✅

---

## Phase 3: 逻辑修复

### 3.1 已知问题
- [ ] 数据库迁移脚本测试
- [ ] AI 识别功能测试
- [ ] 订单状态流转测试

### 3.2 待优化
- [ ] 添加单元测试
- [ ] 添加集成测试

---

## Phase 4: 部署准备

- [ ] requirements.txt 整理
- [ ] .env.example 更新
- [ ] README.md 更新
- [ ] 测试部署

---

## 执行方式

1. 逐项检查并修复
2. 每修复一项进行测试
3. 最终推送部署

---
*Generated: 2026-03-04*
