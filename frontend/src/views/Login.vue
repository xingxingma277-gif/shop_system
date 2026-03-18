<template>
  <div style="max-width:420px;margin:60px auto;">
    <el-card>
      <template #header><b>管理员登录</b></template>
      <el-form label-width="90px">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
      </el-form>
      <div style="display:flex;justify-content:flex-end;">
        <el-button type="primary" @click="submit">登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../api/auth'

const router = useRouter()
const route = useRoute()
const form = reactive({ username: '', password: '' })

async function submit() {
  try {
    const user = await login(form)
    localStorage.setItem('shop:auth_user', user.username)
    localStorage.setItem('shop:auth_display_name', user.display_name)
    ElMessage.success('登录成功')
    router.replace(route.query.redirect || '/admin/users')
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '登录失败')
  }
}
</script>
