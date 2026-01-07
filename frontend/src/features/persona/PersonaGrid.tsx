import React, { useEffect, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { CustomerService } from '../../services/customerService';

const PersonaGrid = () => {
  // Store에서 DB 데이터(customerList)와 선택 액션(setSelectedCustomer)을 가져옴
  const { 
    customerList, 
    setCustomerList, 
    selectedCustomer, 
    setSelectedCustomer 
  } = useAppStore();
  
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 1. 초기 로딩: Supabase에서 데이터 가져오기
  useEffect(() => {
    const loadCustomers = async () => {
      setIsLoading(true);
      try {
        const data = await CustomerService.getCustomers();
        setCustomerList(data);
      } catch (err) {
        console.error("Failed to load customers:", err);
      } finally {
        setIsLoading(false);
      }
    };
    loadCustomers();
  }, [setCustomerList]);

  // 로딩 중 UI
  if (isLoading && customerList.length === 0) {
    return <div className="p-8 text-center text-gray-500 italic">loading data...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {customerList.map((customer) => {
        // DB의 user_id와 현재 선택된 고객의 id 비교
        const isSelected = selectedCustomer?.user_id === customer.user_id;

        // ✅ 보여주기용 데이터: persona_category JSONB 컬럼 사용
        // (데이터가 없을 경우를 대비해 안전하게 optional chaining 사용)
        const displayData = customer.persona_category || {};
        const name = displayData.name || customer.name || 'Unnamed';
        const description = displayData.desc || '설명이 없습니다.';
        const tone = displayData.tone || customer.preferred_tone || 'Neutral';
        const keywords = displayData.keywords || customer.keywords || [];

        return (
          <button
            key={customer.user_id}
            type="button"
            // ✅ 클릭 시 전체 고객 객체를 Store에 저장 (수정 모드 진입)
            onClick={() => setSelectedCustomer(isSelected ? null : customer)} 
            onMouseEnter={() => setHoveredId(customer.user_id)}
            onMouseLeave={() => setHoveredId(null)}
            className={`
              relative p-5 text-left border-2 border-black transition-all duration-200 h-full flex flex-col min-h-[180px]
              ${isSelected
                ? 'bg-yellow-300 translate-x-[2px] translate-y-[2px] shadow-none'
                : 'bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-white/80'
              }
            `}
          >
            {/* 이름 */}
            <h3 className="text-lg font-black mb-1 uppercase italic tracking-tight leading-tight">
              {name}
            </h3>

            {/* 톤 (persona_category 데이터) */}
            <p className="text-xs font-bold text-gray-500 mb-3 border-b-2 border-black/10 pb-1 inline-block">
              {tone}
            </p>

            {/* 설명 (persona_category 데이터) */}
            <p className="text-xs font-medium leading-relaxed mb-4 text-gray-800 flex-1 break-keep">
              {description}
            </p>

            {/* 키워드 (persona_category 데이터) */}
            <div className="flex flex-wrap gap-1 mt-auto pt-2">
              {keywords.slice(0, 5).map((kw: string, idx: number) => (
                <span
                  key={`${customer.user_id}-${kw}-${idx}`}
                  className="text-[10px] font-bold border border-black px-1.5 py-0.5 bg-white whitespace-nowrap"
                >
                  #{kw}
                </span>
              ))}
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default PersonaGrid;