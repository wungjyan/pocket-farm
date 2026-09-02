<template>
  <view class="pf-page legal-page">
    <view class="legal-content">
      <text class="legal-updated-at">更新日期：2026 年 9 月 2 日</text>

      <text class="legal-paragraph">
        掌上农场重视你的个人信息和农场业务数据。本隐私政策说明我们收集的信息、使用方式及你可行使的权利。
      </text>

      <text class="legal-heading">一、我们收集的信息</text>
      <text class="legal-paragraph">
        为提供账号登录服务，我们收集你的手机号。你设置昵称时，我们会保存该昵称用于展示成员身份。
      </text>
      <text class="legal-paragraph">
        你主动创建或录入农场、成员、地块、种养、农事及收获信息时，我们会保存相应业务数据，用于完成农场管理和生产记录功能。
      </text>
      <text class="legal-paragraph">
        你使用 AI 助手时，我们会保存你的对话内容及助手回复，用于展示和管理你的对话历史；为回答问题，相关提问及必要的农场查询数据会发送至 AI 服务提供方处理。
      </text>

      <text class="legal-heading">二、信息的使用与共享</text>
      <text class="legal-paragraph">
        我们仅将上述信息用于账号验证、功能运行、权限控制、数据展示与服务安全。农场数据仅向该农场内具有相应权限的成员展示。
      </text>
      <text class="legal-paragraph">
        我们使用微信小程序平台提供小程序运行与客服能力；使用 AI 助手时，DeepSeek 作为 AI 服务提供方会处理该次请求所必需的内容。除法律法规要求或取得你的另行同意外，我们不会出售你的个人信息。
      </text>

      <text class="legal-heading">三、信息保存与删除</text>
      <text class="legal-paragraph">
        我们在提供服务所必需的期限内保存信息。你可以在 AI 对话管理中删除自己的对话；离开或被移出农场时，该农场下属于你的 AI 对话及消息会被删除，且你不再能够访问该农场数据。
      </text>

      <text class="legal-heading">四、你的权利</text>
      <text class="legal-paragraph">
        你可以在小程序中查看和修改昵称、退出登录、删除自己的 AI 对话；如需咨询、更正或删除其他与你有关的信息，可通过小程序客服联系我们。
      </text>

      <text class="legal-heading">五、政策更新</text>
      <text class="legal-paragraph">
        本政策可能因服务功能或法律要求调整。发生重大变更时，我们将以合理方式向你提示；更新后的政策自公布或提示的生效日期起适用。
      </text>

      <text class="legal-heading">六、联系我们</text>
      <text class="legal-paragraph">
        如你对本隐私政策或个人信息保护有疑问，可通过小程序客服与我们联系。
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
