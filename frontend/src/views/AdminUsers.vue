<template>
  <el-card>
    <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>用户与角色</b><el-button type="primary" @click="openCreateUser">新增用户</el-button></div></template>

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
            <el-table-column label="操作" width="100">
              <template #default="{ row }"><el-button link type="primary" @click="openEditUser(row)">编辑</el-button></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header><div style="display:flex;justify-content:space-between;align-items:center;"><b>角色</b><div><el-button link type="primary" @click="permissionDialog=true">新增权限</el-button><el-button link type="primary" @click="openCreateRole">新增角色</el-button></div></div></template>
          <el-table :data="roles" border>
            <el-table-column prop="code" label="编码" min-width="120" />
            <el-table-column prop="name" label="名称" min-width="120" />
            <el-table-column prop="permission_codes" label="权限" min-width="180">
              <template #default="{ row }">{{ (row.permission_codes || []).join(', ') || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }"><el-button link type="primary" @click="openEditRole(row)">编辑</el-button></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </el-card>

  <el-dialog v-model="userDialog" :title="editingUserId ? '编辑用户' : '新增用户'" width="560px">
    <el-form label-width="100px">
      <el-form-item label="用户名"><el-input v-model="userForm.username" :disabled="!!editingUserId" /></el-form-item>
      <el-form-item label="显示名"><el-input v-model="userForm.display_name" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="userForm.password" type="password" show-password :placeholder="editingUserId ? '不修改可留空' : ''" /></el-form-item>
      <el-form-item label="角色"><el-select v-model="userForm.role_ids" multiple style="width:100%"><el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" /></el-select></el-form-item>
      <el-form-item label="状态" v-if="editingUserId"><el-select v-model="userForm.status" style="width:100%"><el-option label="ACTIVE" value="ACTIVE" /><el-option label="DISABLED" value="DISABLED" /></el-select></el-form-item>
      <el-form-item label="超级管理员"><el-switch v-model="userForm.is_superuser" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="userDialog=false">取消</el-button><el-button type="primary" @click="submitUser">保存</el-button></template>
  </el-dialog>

  <el-dialog v-model="roleDialog" :title="editingRoleId ? '编辑角色' : '新增角色'" width="560px">
    <el-form label-width="100px">
      <el-form-item label="角色编码"><el-input v-model="roleForm.code" :disabled="!!editingRoleId" /></el-form-item>
      <el-form-item label="角色名称"><el-input v-model="roleForm.name" /></el-form-item>
      <el-form-item label="状态" v-if="editingRoleId"><el-select v-model="roleForm.status" style="width:100%"><el-option label="ACTIVE" value="ACTIVE" /><el-option label="DISABLED" value="DISABLED" /></el-select></el-form-item>
      <el-form-item label="权限"><el-select v-model="roleForm.permission_ids" multiple filterable style="width:100%"><el-option v-for="permission in permissions" :key="permission.id" :label="`${permission.name} (${permission.code})`" :value="permission.id" /></el-select></el-form-item>
    </el-form>
    <template #footer><el-button @click="roleDialog=false">取消</el-button><el-button type="primary" @click="submitRole">保存</el-button></template>
  </el-dialog>

  <el-dialog v-model="permissionDialog" title="新增权限" width="560px">
    <el-form label-width="100px">
      <el-form-item label="权限编码"><el-input v-model="permissionForm.code" /></el-form-item>
      <el-form-item label="权限名称"><el-input v-model="permissionForm.name" /></el-form-item>
      <el-form-item label="资源"><el-input v-model="permissionForm.resource" /></el-form-item>
      <el-form-item label="动作"><el-input v-model="permissionForm.action" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="permissionDialog=false">取消</el-button><el-button type="primary" @click="submitPermission">保存</el-button></template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createPermission, createRole, createUser, listPermissions, listRoles, listUsers, updateRole, updateUser } from '../api/admin'

const users = ref([])
const roles = ref([])
const permissions = ref([])
const userDialog = ref(false)
const roleDialog = ref(false)
const permissionDialog = ref(false)
const editingUserId = ref(null)
const editingRoleId = ref(null)
const userForm = reactive({ username: '', display_name: '', password: '', role_ids: [], status: 'ACTIVE', is_superuser: false })
const roleForm = reactive({ code: '', name: '', permission_ids: [], status: 'ACTIVE' })
const permissionForm = reactive({ code: '', name: '', resource: '', action: '' })

function resetUserForm() {
  Object.assign(userForm, { username: '', display_name: '', password: '', role_ids: [], status: 'ACTIVE', is_superuser: false })
}

function resetRoleForm() {
  Object.assign(roleForm, { code: '', name: '', permission_ids: [], status: 'ACTIVE' })
}

function resetPermissionForm() {
  Object.assign(permissionForm, { code: '', name: '', resource: '', action: '' })
}

async function loadAll() {
  users.value = await listUsers({})
  roles.value = await listRoles({})
  permissions.value = await listPermissions()
}

function openCreateUser() {
  editingUserId.value = null
  resetUserForm()
  userDialog.value = true
}

function openEditUser(row) {
  editingUserId.value = row.id
  Object.assign(userForm, {
    username: row.username,
    display_name: row.display_name,
    password: '',
    role_ids: [...(row.role_ids || [])],
    status: row.status,
    is_superuser: !!row.is_superuser,
  })
  userDialog.value = true
}

function openCreateRole() {
  editingRoleId.value = null
  resetRoleForm()
  roleDialog.value = true
}

function openEditRole(row) {
  editingRoleId.value = row.id
  Object.assign(roleForm, {
    code: row.code,
    name: row.name,
    permission_ids: [...(row.permission_ids || [])],
    status: row.status,
  })
  roleDialog.value = true
}

async function submitUser() {
  try {
    const payload = { ...userForm }
    if (editingUserId.value && !payload.password) delete payload.password
    if (editingUserId.value) await updateUser(editingUserId.value, payload)
    else await createUser(payload)
    ElMessage.success(editingUserId.value ? '用户已更新' : '用户已创建')
    userDialog.value = false
    resetUserForm()
    await loadAll()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  }
}

async function submitRole() {
  try {
    const payload = { ...roleForm }
    if (editingRoleId.value) await updateRole(editingRoleId.value, payload)
    else await createRole(payload)
    ElMessage.success(editingRoleId.value ? '角色已更新' : '角色已创建')
    roleDialog.value = false
    resetRoleForm()
    await loadAll()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  }
}

async function submitPermission() {
  try {
    await createPermission({ ...permissionForm })
    ElMessage.success('权限已创建')
    permissionDialog.value = false
    resetPermissionForm()
    await loadAll()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '保存失败')
  }
}

onMounted(loadAll)
</script>
