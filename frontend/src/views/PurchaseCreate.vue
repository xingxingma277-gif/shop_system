<template>
  <div class="purchase-create">                                            <el-card shadow="never" style="border-radius: 8px;">                   <template #header>                                                   <div style="display: flex; justify-content: space-between; align-items: center;"> <span style="font-weight: 700; font-size: 16px;">新建采购单 (Purchase Order)</span> <el-button @click="router.push('/purchases')">返回列表</el-button> </div>
      </template>

      <el-form label-width="100px" style="margin-bottom: 20px; background: #f8f9fa; padding: 20px; border-radius: 8px;"> <el-row :gutter="20">                                              <el-col :span="8">                                               <el-form-item label="供应商" required>                         <el-select v-model="form.supplier_id" filterable placeholder="请选择上游供应商" style="width: 100%;"> <el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" /> </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">                                               <el-form-item label="预计到货">                                <el-date-picker v-model="form.expected_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%;" /> </el-form-item>
          </el-col>
          <el-col :span="8">                                               <el-form-item label="采购备注">                                <el-input v-model="form.remark" placeholder="如：加急发货、物流要求等..." /> </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div style="margin-bottom: 16px;">                                   <el-button type="primary" plain @click="addRow">+ 添加采购物资明细</el-button> </div>

      <el-table :data="form.items" border style="margin-bottom: 20px;">    <el-table-column type="index" label="序号" width="60" align="center" /> <el-table-column label="商品 (Stock Keeping Unit)" min-width="260"> <template #default="{ row }">                                    <el-select v-model="row.product_id" filterable remote :remote-method="searchProducts" placeholder="拼音/名称搜索商品" style="width: 100%;" @change="(val) => handleProductChange(val, row)"> <el-option v-for="p in catalog.products" :key="p.id" :label="p.name" :value="p.id"> <span style="float: left">{{ p.name }}</span>              <span style="float: right; color: #8492a6; font-size: 13px;">库存: {{ p.stock_quantity }} {{ p.unit }}</span> </el-option>
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="采购数量" width="160">                     <template #default="{ row }">                                    <el-input-number v-model="row.qty" :min="1" @change="calculateTotal" style="width: 100%;" /> </template>
        </el-table-column>
        <el-table-column label="预计进货价" width="160">                   <template #default="{ row }">                                    <el-input-number v-model="row.unit_price" :min="0" :precision="2" :step="1" @change="calculateTotal" style="width: 100%;" /> </template>
        </el-table-column>
        <el-table-column label="金额小计" width="140" align="right">       <template #default="{ row }">                                    <span style="color: #f56c6c; font-weight: bold;">¥ {{ ((row.qty || 0) * (row.unit_price || 0)).toFixed(2) }}</span> </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">           <template #default="{ $index }">                                 <el-button type="danger" link @click="removeRow($index)">删除</el-button> </template>
        </el-table-column>
      </el-table>

      <div style="display: flex; justify-content: flex-end; align-items: center; padding: 20px; background: #f8f9fa; border-radius: 8px;"> <span style="font-size: 16px; margin-right: 16px;">合计金额：<span style="font-size: 24px; color: #f56c6c; font-weight: bold;">¥ {{ totalAmount.toFixed(2) }}</span></span> <el-button type="success" size="large" @click="submitOrder" :loading="isSubmitting">确认无误，提交采购申请</el-button> </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'                             // 引入 Vue 的响应式 API 和生命周期钩子
import { useRouter } from 'vue-router'                                     // 引入 Vue 路由工具
import { ElMessage } from 'element-plus'                                   // 引入 Element Plus 的消息提示组件
import { useCatalogStore } from '../stores/catalog'                        // 引入商品目录状态库
import http from '../api/http'                                             // 引入封装好的 HTTP 请求工具

const router = useRouter()                                                 // 实例化路由控制器
const catalog = useCatalogStore()                                          // 实例化商品目录状态库

const isSubmitting = ref(false)                                            // 控制提交按钮的加载状态
const totalAmount = ref(0)                                                 // 存储订单总金额
const suppliers = ref([])                                                  // 存储供应商列表数据

const form = reactive({                                                    // 声明包含表单所有数据的响应式对象
  supplier_id: null,                                                       // 选中的供应商 ID
  expected_date: '',                                                       // 预计到货日期
  remark: '',                                                              // 采购单备注
  items: [{ product_id: null, qty: 1, unit_price: 0 }]                     // 采购明细数组，默认包含一个空行
})

const fetchSuppliers = async () => {                                       // 获取供应商列表的异步函数
  try {
    const res = await http.get('/api/suppliers?limit=1000')                // 发起 GET 请求获取供应商数据
    suppliers.value = res.data.items || res.data                           // 将数据赋值给 suppliers 变量
  } catch (e) {
    ElMessage.error('获取供应商列表失败')                                  // 请求失败时弹出错误提示
  }
}

const searchProducts = async (q) => {                                      // 远程搜索商品的函数
  await catalog.searchProducts(q || '')                                    // 调用 catalog store 的搜索方法
}

const handleProductChange = (productId, row) => {                          // 当商品下拉框选中值改变时触发
  const product = catalog.products.find(p => p.id === productId)           // 在当前商品列表中查找选中的商品
  if (product) {
    row.unit_price = product.standard_price || 0                           // 自动带出该商品的系统标准售价作为参考进货价
  }
  calculateTotal()                                                         // 重新计算总金额
}

const addRow = () => {                                                     // 添加明细行的函数
  form.items.push({ product_id: null, qty: 1, unit_price: 0 })             // 向明细数组推入一个初始化的空对象
}

const removeRow = (index) => {                                             // 删除明细行的函数
  form.items.splice(index, 1)                                              // 根据索引从数组中移除该行
  if (form.items.length === 0) addRow()                                    // 如果全删光了，自动补一个空行，防止表格完全空白
  calculateTotal()                                                         // 重新计算总金额
}

const calculateTotal = () => {                                             // 计算整单总金额的函数
  totalAmount.value = form.items.reduce((sum, item) => sum + (item.qty || 0) * (item.unit_price || 0), 0) // 使用 reduce 方法累加每一行的小计
}

const submitOrder = async () => {                                          // 提交采购单的函数
  if (!form.supplier_id) return ElMessage.warning('请选择上游供应商')      // 校验：必须选择供应商
  const validItems = form.items.filter(i => i.product_id)                  // 过滤出真正选择了商品的有效行
  if (validItems.length === 0) return ElMessage.warning('请至少添加一件采购物资') // 校验：必须有有效商品明细

  isSubmitting.value = true                                                // 开启提交按钮的 loading 动画防重复点击
  try {
    const payload = {                                                      // 组装发送给后端的请求体 (Payload)
      supplier_id: form.supplier_id,                                       // 提取供应商 ID
      expected_date: form.expected_date || null,                           // 提取预计到货日期
      remark: form.remark,                                                 // 提取备注
      total_amount: totalAmount.value,                                     // 提取总金额
      items: validItems.map(i => ({                                        // 映射有效明细行，只保留后端需要的核心字段
        product_id: i.product_id,
        qty: i.qty,
        unit_price: i.unit_price
      }))
    }
    await http.post('/api/purchases', payload)                             // 发起 POST 请求创建采购单
    ElMessage.success('采购单创建成功！即将返回列表...')                   // 成功提示
    router.push('/purchases')                                              // 跳转回采购单列表页
  } catch (e) {
    ElMessage.error('采购单提交失败，请检查网络或联系技术支持')            // 失败提示
  } finally {
    isSubmitting.value = false                                             // 无论成功失败，关闭 loading 动画
  }
}

onMounted(() => {                                                          // 组件挂载完毕后的生命周期钩子
  fetchSuppliers()                                                         // 初始加载供应商列表
  searchProducts('')                                                       // 初始加载默认商品列表
})
</script>