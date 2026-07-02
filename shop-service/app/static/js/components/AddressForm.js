window.AddressForm = {
  props: {
    form: {
      type: Object,
      required: true,
    },
    showSaveToProfile: {
      type: Boolean,
      default: false,
    },
    saveToProfile: {
      type: Boolean,
      default: false,
    },
    showDefault: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['update:saveToProfile'],
  template: `
    <div class="space-y-3">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">收货人</label>
          <input v-model="form.receiver_name" placeholder="姓名"
                 class="input-shadow w-full px-3 py-2 border border-orange-200/60 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400/40"/>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">手机号</label>
          <input v-model="form.phone" placeholder="手机号"
                 class="input-shadow w-full px-3 py-2 border border-orange-200/60 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400/40"/>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">省份</label>
          <input v-model="form.province" placeholder="省"
                 class="input-shadow w-full px-3 py-2 border border-orange-200/60 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400/40"/>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">城市</label>
          <input v-model="form.city" placeholder="市"
                 class="input-shadow w-full px-3 py-2 border border-orange-200/60 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400/40"/>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1">区县</label>
          <input v-model="form.district" placeholder="区"
                 class="input-shadow w-full px-3 py-2 border border-orange-200/60 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400/40"/>
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 mb-1">详细地址</label>
        <input v-model="form.detail" placeholder="街道、门牌号等"
               class="input-shadow w-full px-3 py-2 border border-orange-200/60 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400/40"/>
      </div>

      <label v-if="showSaveToProfile" class="flex items-center gap-2 cursor-pointer pt-1">
        <input type="checkbox"
               :checked="saveToProfile"
               @change="$emit('update:saveToProfile', $event.target.checked)"
               class="w-4 h-4 rounded accent-orange-500"/>
        <span class="text-sm text-gray-600">保存到个人中心收货地址</span>
      </label>

      <label v-if="showDefault" class="flex items-center gap-2 cursor-pointer pt-1">
        <input type="checkbox" v-model="form.is_default" class="w-4 h-4 rounded accent-orange-500"/>
        <span class="text-sm text-gray-600">设为默认地址</span>
      </label>
    </div>
  `
};
