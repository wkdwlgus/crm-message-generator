import { useState } from 'react';

interface AddPersonaModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (schema: string) => void;
}

export function AddPersonaModal({ isOpen, onClose, onApply }: AddPersonaModalProps) {
  const [selectedSchema, setSelectedSchema] = useState('기본 스키마');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white border-[4px] border-black p-6 w-full max-auto shadow-[12px_12px_0px_0px_rgba(0,0,0,1)] max-w-sm">
        <h2 className="text-xl font-black mb-6 tracking-tighter uppercase">Add New Persona</h2>
        
        <div className="mb-8">
          <label className="text-[10px] font-black mb-2 block uppercase">Select Schema</label>
          <select 
            value={selectedSchema}
            onChange={(e) => setSelectedSchema(e.target.value)}
            className="w-full border-[3px] border-black p-3 font-bold bg-yellow-50 focus:outline-none"
          >
            <option value="기본 스키마">기본 스키마</option>
            <option value="민감성 스키마">민감성 스키마 (CS 강조)</option>
            <option value="이벤트형 스키마">이벤트형 (혜택 강조)</option>
          </select>
        </div>

        <div className="flex gap-4">
          <button 
            onClick={onClose}
            className="flex-1 py-3 border-[3px] border-black font-black hover:bg-gray-100"
          >
            CANCEL
          </button>
          <button 
            onClick={() => onApply(selectedSchema)}
            className="flex-1 py-3 border-[3px] border-black bg-green-400 font-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-1 active:translate-y-1"
          >
            APPLY
          </button>
        </div>
      </div>
    </div>
  );
}