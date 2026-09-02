<template>
  <view class="pf-page legal-page">
    <view class="legal-content">
      <text class="legal-updated-at">更新日期：2026 年 9 月 2 日</text>

      <text class="legal-paragraph">
        欢迎使用掌农记。请在使用本服务前认真阅读本协议；登录或使用本服务，即表示你已阅读、理解并同意本协议。
      </text>

      <text class="legal-heading">一、服务内容</text>
      <text class="legal-paragraph">
        掌农记提供农场、地块、种养、农事、收获记录及相关查询服务。AI 助手当前仅提供农场数据查询，不会代替你新建、修改或删除业务记录。
      </text>

      <text class="legal-heading">二、账号与使用</text>
      <text class="legal-paragraph">
        你使用手机号验证登录并管理自己的账号。请妥善保管登录设备，不得利用本服务实施违法违规行为，或干扰、破坏服务的正常运行。
      </text>

      <text class="legal-heading">三、农场数据与成员权限</text>
      <text class="legal-paragraph">
        你可在获授权的农场内创建和查看业务数据。农场成员的可见范围及操作权限由农场角色决定；离开或被移出农场后，你将无法继续访问该农场的数据。
      </text>

      <text class="legal-heading">四、AI 服务</text>
      <text class="legal-paragraph">
        使用 AI 助手时，请勿输入与农场查询无关的敏感个人信息。AI 回复仅供辅助参考，不构成农业生产、医疗、法律或其他专业建议；重要决策请结合实际情况自行判断。
      </text>

      <text class="legal-heading">五、服务调整</text>
      <text class="legal-paragraph">
        我们可能基于服务运营、安全或法律要求调整本服务。本协议发生重大变更时，将以合理方式向你提示；继续使用服务即视为接受更新后的协议。
      </text>

      <text class="legal-heading">六、联系我们</text>
      <text class="legal-paragraph">
        如你对本协议或服务有疑问，可通过小程序客服与我们联系。
      </text>
      <button class="legal-contact pf-tappable" open-type="contact">联系客服</button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.legal-page {
  min-height: 100vh;
}

.legal-content {
  padding: $pf-space-5 $pf-space-page-x calc($pf-space-page-bottom + env(safe-area-inset-bottom));
}

.legal-updated-at,
.legal-heading,
.legal-paragraph {
  display: block;
}

.legal-updated-at {
  margin-bottom: $pf-space-6;
  color: $pf-color-text-muted;
  font-size: 24rpx;
}

.legal-heading {
  margin-top: $pf-space-6;
  color: $pf-color-text;
  font-size: 29rpx;
  font-weight: 650;
  line-height: 1.5;
}

.legal-paragraph {
  margin-top: $pf-space-2;
  color: $pf-color-text-secondary;
  font-size: 27rpx;
  line-height: 1.8;
}

.legal-contact {
  width: 100%;
  height: 88rpx;
  margin-top: $pf-space-3;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  color: $pf-color-primary;
  font-size: 27rpx;
  font-weight: 600;
  line-height: 86rpx;
}

.legal-contact::after {
  border: 0;
}
</style>
