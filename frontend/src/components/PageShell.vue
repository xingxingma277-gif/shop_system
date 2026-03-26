<template>
  <div class="page-shell">                                      <div class="page-header">                                   <div class="page-title-area">                             <h2 class="page-title">{{ title }}</h2>                 <span class="page-subtitle" v-if="subtitle">            {{ subtitle }}
        </span>
      </div>
      <div class="page-actions">                                <slot name="actions"></slot>                            </div>
    </div>

    <div class="page-filters" v-if="$slots.filters">            <slot name="filters"></slot>                              </div>

    <div class="page-content" :class="{ 'no-padding': disablePadding }"> <slot></slot>                                             </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'                               // 引入组件属性定义 API (Application Programming Interface，应用程序接口)

defineProps({
  title: { type: String, required: true },                      // 页面主标题，必填
  subtitle: { type: String, default: '' },                      // 页面副标题解释，选填
  disablePadding: { type: Boolean, default: false }             // 是否禁用主内容区的默认内边距，常用于全屏表格
})
</script>

<style scoped>
.page-shell {
  display: flex;                                                /* 启用弹性盒子模型 */
  flex-direction: column;                                       /* 垂直方向排列子元素 */
  gap: 16px;                                                    /* 元素之间的标准间距为 16px */
  padding: 16px;                                                /* 页面整体外边距 */
  height: 100%;                                                 /* 占满父容器高度 */
  box-sizing: border-box;                                       /* 边框计算入宽高 */
}

.page-header {
  display: flex;                                                /* 标题栏启用弹性盒 */
  justify-content: space-between;                               /* 标题和操作按钮两端对齐 */
  align-items: center;                                          /* 垂直方向居中对齐 */
}

.page-title-area {
  display: flex;                                                /* 标题与副标题水平排列 */
  align-items: baseline;                                        /* 基线对齐，确保文字底部在一条平齐线上 */
  gap: 12px;                                                    /* 标题与副标题间距 */
}

.page-title {
  margin: 0;                                                    /* 重置默认边距 */
  font-size: 20px;                                              /* 设定标准标题字号 */
  font-weight: 600;                                             /* 设定字重为半粗体 */
  color: #303133;                                               /* 设定标准主标题颜色 */
}

.page-subtitle {
  color: #909399;                                               /* 副标题采用次级灰色 */
  font-size: 13px;                                              /* 较小的辅助说明字号 */
}

.page-filters {
  background: #f8f9fa;                                          /* 筛选区采用浅灰底色进行视觉隔离 */
  padding: 16px 16px 0 16px;                                    /* 内部留白，底部设为0以贴合 ElForm 默认边距 */
  border-radius: 4px;                                           /* 轻微圆角 */
  border: 1px solid #ebeef5;                                    /* 极浅灰边框 */
}

.page-content {
  background: #ffffff;                                          /* 内容区纯白底色 */
  padding: 16px;                                                /* 标准内边距 */
  border-radius: 4px;                                           /* 标准圆角 */
  border: 1px solid #ebeef5;                                    /* 外围边框定义层级 */
  flex: 1;                                                      /* 占据剩余的全部纵向空间 */
  overflow: auto;                                               /* 内容溢出时出现滚动条 */
}

.page-content.no-padding {
  padding: 0;                                                   /* 移除内边距的修饰类 */
}
</style>