<template>
  <view class="pf-page members-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#006C49" />
      <text>正在加载成员</text>
    </view>

    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 24rpx; border-radius: 16rpx;"
        @click="loadMembers"
      >
        重试
      </uv-button>
    </view>

    <template v-else>
      <view class="member-section">
        <text class="section-label">成员</text>
        <view class="member-list pf-card">
          <view v-for="member in members" :key="member.id" class="member-row">
            <view class="member-avatar">
              <text>{{ avatarText(member) }}</text>
            </view>
            <view class="member-copy">
              <view class="member-name-line">
                <text class="member-name">{{ displayName(member) }}</text>
                <text v-if="member.userId === currentUserId" class="self-badge">我</text>
              </view>
              <text class="member-joined">加入于 {{ formatDate(member.joinedAt) }}</text>
            </view>

            <picker
              v-if="canManage(member)"
              mode="selector"
              :range="roleLabels"
              :value="roleIndex(member.role)"
              @change="handleRoleChange(member, $event)"
            >
              <view class="role-control">
                <text>{{ roleLabel(member.role) }}</text>
                <uv-icon name="arrow-down" size="14" color="#748178" />
              </view>
            </picker>
            <text v-else class="role-text">{{ roleLabel(member.role) }}</text>
            <view
              v-if="canManage(member)"
              class="remove-control pf-tappable"
              @tap.stop="handleRemove(member)"
            >
              <uv-icon name="trash" size="18" color="#A9433B" />
            </view>
          </view>
        </view>
      </view>

      <view v-if="canManageMembers" class="add-section">
        <text class="section-label">添加成员</text>
        <view class="field-group">
          <text class="field-label">手机号</text>
          <view class="input-shell" :class="{ 'input-shell--focused': phoneFocused }">
            <uv-input
              v-model="phoneNumber"
              type="number"
              maxlength="11"
              clearable
              border="none"
              placeholder="请输入 11 位手机号"
              placeholder-style="color: #748178;"
              color="#17261F"
              @focus="phoneFocused = true"
              @blur="phoneFocused = false"
            />
          </view>
        </view>

        <view class="field-group">
          <text class="field-label">加入角色</text>
          <picker
            mode="selector"
            :range="roleLabels"
            :value="addRoleIndex"
            @change="handleAddRoleChange"
          >
            <view class="select-shell">
              <text>{{ roleLabels[addRoleIndex] }}</text>
              <uv-icon name="arrow-down" size="16" color="#748178" />
            </view>
          </picker>
        </view>

        <uv-button
          type="primary"
          shape="square"
          :loading="adding"
          loading-text="添加中"
          custom-style="height: 96rpx; margin-top: 40rpx; border-radius: 16rpx;"
          @click="handleAdd"
        >
          添加成员
        </uv-button>
      </view>

    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import {
  addFarmMember,
  getFarm,
  getFarmMembers,
  removeFarmMember,
  updateFarmMember,
  type Farm,
  type FarmMember,
  type FarmRole,
} from "../../services/farm";
import { getCurrentUser } from "../../services/user";

const farmId = ref(0);
const farm = ref<Farm | null>(null);
const members = ref<FarmMember[]>([]);
const currentUserId = ref(0);
const loading = ref(true);
const adding = ref(false);
const loadError = ref("");
const phoneNumber = ref("");
const phoneFocused = ref(false);
const addRoleIndex = ref(0);
const toastRef = ref<{
  error: (message: string) => void;
  success: (message: string) => void;
} | null>(null);
const canManageMembers = computed(
  () => farm.value?.myRole === "OWNER" || farm.value?.myRole === "ADMIN",
);
const roleValues = computed<FarmRole[]>(() =>
  farm.value?.myRole === "OWNER" ? ["OWNER", "ADMIN", "MEMBER"] : ["ADMIN", "MEMBER"],
);
const roleLabels = computed(() => roleValues.value.map(roleLabel));

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function roleLabel(role: FarmRole): string {
  if (role === "OWNER") return "农场主";
  if (role === "ADMIN") return "管理员";
  return "成员";
}

function displayName(member: FarmMember): string {
  return member.nickname?.trim() || "未设置昵称";
}

function avatarText(member: FarmMember): string {
  return displayName(member).slice(0, 1);
}

function formatDate(value: string): string {
  const date = new Date(value.replace(" ", "T") + (value.includes("Z") ? "" : "Z"));
  if (Number.isNaN(date.getTime())) return "未知日期";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function canManage(member: FarmMember): boolean {
  if (!canManageMembers.value || member.userId === currentUserId.value) return false;
  if (farm.value?.myRole === "ADMIN" && member.role === "OWNER") return false;
  return true;
}

function roleIndex(role: FarmRole): number {
  const index = roleValues.value.indexOf(role);
  return index >= 0 ? index : roleValues.value.length - 1;
}

function handleAddRoleChange(event: { detail: { value: number | string } }): void {
  addRoleIndex.value = Number(event.detail.value);
}

async function loadMembers(): Promise<void> {
  if (!farmId.value) {
    loadError.value = "农场信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const [farmResult, memberPage, user] = await Promise.all([
      getFarm(farmId.value),
      getFarmMembers(farmId.value),
      getCurrentUser(),
    ]);
    farm.value = farmResult;
    members.value = memberPage.items;
    currentUserId.value = user.id;
    addRoleIndex.value = 0;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "成员加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

async function handleAdd(): Promise<void> {
  const phone = phoneNumber.value.trim();
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    toastRef.value?.error("请输入正确的手机号");
    return;
  }
  adding.value = true;
  try {
    await addFarmMember(farmId.value, phone, roleValues.value[addRoleIndex.value]);
    phoneNumber.value = "";
    toastRef.value?.success("成员添加成功");
    await loadMembers();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "添加失败，请稍后再试");
    }
  } finally {
    adding.value = false;
  }
}

async function handleRoleChange(
  member: FarmMember,
  event: { detail: { value: number | string } },
): Promise<void> {
  const nextRole = roleValues.value[Number(event.detail.value)];
  if (!nextRole || nextRole === member.role) return;
  try {
    const updated = await updateFarmMember(farmId.value, member.id, nextRole);
    const index = members.value.findIndex((item) => item.id === member.id);
    if (index >= 0) members.value[index] = updated;
    toastRef.value?.success("角色已更新");
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "角色修改失败，请稍后再试");
    }
  }
}

function handleRemove(member: FarmMember): void {
  uni.showModal({
    title: "移除成员",
    content: `确定移除“${displayName(member)}”吗？`,
    confirmColor: "#A9433B",
    success: async (result) => {
      if (!result.confirm) return;
      try {
        await removeFarmMember(farmId.value, member.id);
        members.value = members.value.filter((item) => item.id !== member.id);
        uni.showToast({ title: "成员已移除", icon: "none" });
      } catch (error) {
        if (error instanceof ApiRequestError && error.statusCode === 401) {
          handleUnauthorized();
        } else {
          toastRef.value?.error(error instanceof ApiRequestError ? error.message : "移除失败，请稍后再试");
        }
      }
    },
  });
}

onLoad((options) => {
  farmId.value = Number(options?.farmId || 0);
});

onShow(() => {
  if (farmId.value) loadMembers();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.members-page {
  padding: $pf-space-4 $pf-space-page-x $pf-space-page-bottom;
}

.member-list {
  overflow: hidden;
}

.member-row {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 24rpx;
}

.member-row + .member-row {
  border-top: 1rpx solid $pf-color-divider;
}

.member-avatar {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: $pf-radius-control;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: $pf-font-size-title;
  font-weight: 650;
}

.member-copy {
  min-width: 0;
  flex: 1;
  margin: 0 $pf-space-2;
}

.member-name-line {
  display: flex;
  align-items: center;
}

.member-name {
  max-width: 270rpx;
  overflow: hidden;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.self-badge {
  margin-left: $pf-space-1;
  padding: 4rpx 10rpx;
  border-radius: $pf-radius-pill;
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-caption;
}

.member-joined {
  display: block;
  margin-top: 4rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-caption;
}

.role-control {
  display: flex;
  min-width: 120rpx;
  min-height: 56rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  padding: 0 14rpx;
  border-radius: $pf-radius-control;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: $pf-font-size-label;
  font-weight: 600;
}

.role-control text {
  margin-right: $pf-space-1;
}

.role-text {
  min-width: 120rpx;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-label;
  text-align: center;
}

.remove-control {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  align-items: center;
  justify-content: flex-end;
  margin-left: $pf-space-1;
}

.section-label {
  display: block;
  margin: 0 4rpx $pf-space-2;
  color: $pf-color-text;
  font-size: $pf-font-size-section;
  font-weight: 720;
}

.add-section {
  margin-top: $pf-space-6;
}

.field-group + .field-group {
  margin-top: $pf-space-4;
}

.field-label {
  display: block;
  margin: 0 4rpx $pf-space-2;
  color: $pf-color-text;
  font-size: $pf-font-size-body;
  font-weight: 650;
}

.input-shell {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 24rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.input-shell--focused {
  border-color: $pf-color-primary;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}

.select-shell {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  padding: 0 24rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  color: $pf-color-text;
  font-size: $pf-font-size-body;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
