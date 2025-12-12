/**
 * ChannelSelector Component
 * 메시지 채널 선택 컴포넌트
 */
import type { ChannelType } from '../types/api';

interface ChannelSelectorProps {
  selected: ChannelType;
  onSelect: (channel: ChannelType) => void;
  disabled?: boolean;
}

export function ChannelSelector({ selected, onSelect, disabled = false }: ChannelSelectorProps) {
  const channels: { value: ChannelType; label: string; icon: string }[] = [
    { value: 'SMS', label: 'SMS', icon: '📱' },
    { value: 'KAKAO', label: '카카오톡', icon: '💬' },
    { value: 'EMAIL', label: '이메일', icon: '📧' },
  ];

  return (
    <div className="w-full max-w-md">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        메시지 채널 선택
      </label>
      <div className="flex gap-2">
        {channels.map((channel) => (
          <button
            key={channel.value}
            onClick={() => onSelect(channel.value)}
            disabled={disabled}
            className={`
              flex-1 px-4 py-3 rounded-lg border-2 transition-all
              ${selected === channel.value
                ? 'border-pink-500 bg-pink-50 text-pink-700'
                : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="text-2xl mb-1">{channel.icon}</div>
            <div className="text-sm font-medium">{channel.label}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
