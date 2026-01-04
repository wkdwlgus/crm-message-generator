/**
 * ChannelSelector Component
 */
import type { ChannelType } from '../types/api';


interface ChannelSelectorProps {
  selected: ChannelType | null;
  onSelect: (channel: ChannelType | null) => void;
  disabled?: boolean;
}

export function ChannelSelector({ selected, onSelect, disabled = false }: ChannelSelectorProps) {
  // 아이콘과 라벨 설정
  const channels: { id: ChannelType; label: string; icon: string }[] = [
    { id: 'APP_PUSH', label: ' APP_PUSH', icon: '📱' },
    { id: 'SMS', label: ' SMS', icon: '💬' },
    { id: 'KAKAO', label: ' KAKAO', icon: '💛' },
    { id: 'EMAIL', label: ' EMAIL', icon: '📧' },
  ];


  return (
    <div className="grid grid-cols-2 gap-2 w-full">
      {channels.map((ch) => (
        <button
          key={ch.id}
          onClick={() => onSelect(selected === ch.id ? null : ch.id)}
          disabled={disabled}
          className={`
            w-full py-3 px-4 border-2 border-black transition-all
            text-xs font-black
            ${selected === ch.id 
              ? 'bg-yellow-300 shadow-none translate-x-1 translate-y-1' 
              : 'bg-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]  hover:-translate-y-1 hover:bg-yellow-50'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          <span className="text-sm">{ch.icon}</span>
          <span>{ch.label}</span>
        </button>
      ))}
    </div>
  );
}
