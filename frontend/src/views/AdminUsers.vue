<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>用户与角色</b><el-button type="primary" @click="userDialog=true">新增用户</el-button></div></template>

    <el-row :gutter="12">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>用户</b><el-button link type="primary" @click="loadAll">刷新</el-button></div></template>
          <el-table :data="users" border>
            <el-table-column prop="username" label="用户名" min-width="120" />
            <el-table-column prop="display_name" label="显示名" min-width="120" />
            <el-table-column prop="role_names" label="角色" min-width="160">
              <template #default="{ row }">{{ (row.role_names || []).join(' / ') || '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>角色</b><el-button link type="primary" @click="roleDialog=true">新增角色</el-button></div></template>
          <el-table :data="roles" border>
            <el-table-column prop="code" label="编码" min-width="120" />
            <el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column prop="permission_codes" label="权限" min-width="180">
              <template #default="{ row }">{{ (row.permission_codes || []).join(', ') || '-' }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </el-card>

  <el-dialog v-model="userDialog" title="新增用户" width="560px">
    <el-form label-width="100px">
      <el-form-item label="用户名"><el-input v-model="userForm.username" /></el-form-item>
      <el-form-item label="显示名"><el-input v-model="userForm.display_name" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="userForm.password" type="password" show-password /></el-form-item>
      <el-form-item label="角色"><el-select v-model="userForm.role_ids" multiple style="width:100%"><el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" /></el-select></el-form-item>
    </el-form>
    <template #footer><el-button @click="userDialog=false">取消</el-button><el-button type="primary" @click="submitUser">保存</el-button></template>
  </el-dialog>

  <el-dialog v-model="roleDialog" title="新增角色" width="560px">
    <el-form label-width="100px">
      <el-form-item label="角色编码"><el-input v-model="roleForm.code" /></el-form-item>
      <el-form-item label="角色名称"><el-input v-model="roleForm.name" /></el-form-item>
      <el-form-item label="权限"><el-select v-model="roleForm.permission_ids" multiple style="width:100%"><el-option v-for="permission in permissions" :key="permission.id" :label="permission.name" :value="permission.id" /></el-select></el-form-item>
    </el-form>
    <template #footer><el-button @click="roleDialog=false">取消</el-button><el-button type="primary" @click="submitRole">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createRole, createUser, listPermissions, listRoles, listUsers } from '../api/admin'

const users = ref([])
const roles = ref([])
const permissions = ref([])
const userDialog = ref(false)
const roleDialog = ref(false)
const userForm = reactive({ username: '', display_name: '', password: '', role_ids: [] })
const roleForm = reactive({ code: '', name: '', permission_ids: [] })

async function loadAll() {
  users.value = await listUsers({})
  roles.value = await listRoles({})
  permissions.value = await listPermissions()
}

async function submitUser() {
  try {
    await createUser({ ...userForm })
    ElMessage.success('用户已创建')
    userDialog.value = false
    userForm.username = ''
    userForm.display_name = ''
    userForm.password = ''
    userForm.role_ids = []
    await loadAll()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '创建失败')
  }
}

async function submitRole() {
  try {
    await createRole({ ...roleForm })
    ElMessage.success('角色已创建')
    roleDialog.value = false
    roleForm.code = ''
    roleForm.name = ''
    roleForm.permission_ids = []
    await loadAll()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '创建失败')
  }
}

onMounted(loadAll)
</script>
