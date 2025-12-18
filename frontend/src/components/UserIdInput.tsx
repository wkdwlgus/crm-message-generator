import { useState, useEffect } from 'react';

interface UserIdInputProps {
  onChange: (userId: string) => void;
  disabled?: boolean;
  initialValue?: string;
}

export function UserIdInput({ onChange, disabled = false, initialValue = '' }: UserIdInputProps) {
  const [userId, setUserId] = useState(initialValue);

  // 입력값이 바뀔 때마다 부모에게 전달
  useEffect(() => {
    onChange(userId.trim());
  }, [userId, onChange]);

  return (
    <div className="w-full space-y-2">
      <div className="flex flex-col gap-2 text-left">
        <label className="text-[10px] font-black text-black ml-1 uppercase">User ID Database</label>
        <input
          type="text"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="ENTER USER ID..."
          disabled={disabled}
          className="w-full px-4 py-3 border-[3px] border-black rounded-none focus:outline-none focus:bg-yellow-50 disabled:bg-gray-200 font-mono text-sm shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
        />
      </div>
    </div>
  );
}