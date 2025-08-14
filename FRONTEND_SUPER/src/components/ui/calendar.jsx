

import React, { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

// Simple utility function to combine class names
const cn = (...classes) => classes.filter(Boolean).join(" ");

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  mode = "single",
  selected,
  onSelect,
  ...props
}) {
  // Internal state for selected date if not provided externally
  const [internalSelected, setInternalSelected] = useState(null);
  
  // Use provided selected/onSelect props if available, otherwise use internal state
  const selectedDate = selected !== undefined ? selected : internalSelected;
  const handleSelect = onSelect || setInternalSelected;
  
  // Mock DayPicker structure
  const currentDate = new Date();
  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();
  
  // Generate days for the current month
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();
  
  // Create calendar grid
  const renderCalendar = () => {
    const days = [];
    const weekRows = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(
        <div 
          key={`empty-${i}`} 
          className="h-9 w-9 text-center text-sm p-0 opacity-50"
        >
          <button className="h-9 w-9 p-0 font-normal text-slate-400" disabled>
            {new Date(currentYear, currentMonth, -firstDayOfMonth + i + 1).getDate()}
          </button>
        </div>
      );
    }
    
    // Add cells for each day of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(currentYear, currentMonth, day);
      const isSelected = selectedDate && date.toDateString() === selectedDate.toDateString();
      const isToday = date.toDateString() === new Date().toDateString();
      
      days.push(
        <div 
          key={`day-${day}`}
          className={cn(
            "h-9 w-9 text-center text-sm p-0 relative",
            isSelected ? "bg-blue-100 rounded-md" : ""
          )}
        >
          <button 
            onClick={() => handleSelect(date)}
            className={cn(
              "h-9 w-9 p-0 font-normal",
              isSelected ? "bg-blue-500 text-white rounded-md" : "",
              isToday && !isSelected ? "bg-slate-200 rounded-md" : ""
            )}
          >
            {day}
          </button>
        </div>
      );
    }
    
    // Group days into weeks
    for (let i = 0; i < days.length; i += 7) {
      weekRows.push(
        <div key={`week-${i}`} className="flex w-full mt-2">
          {days.slice(i, i + 7)}
        </div>
      );
    }
    
    return weekRows;
  };

  // Day name headers
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  
  return (
    <div className={cn("p-3", className)}>
      <div className="flex justify-center pt-1 relative items-center">
        <button className="absolute left-1 h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100">
          <ChevronLeft className="h-4 w-4" />
        </button>
        
        <div className="text-sm font-medium">
          {new Date(currentYear, currentMonth).toLocaleString('default', { month: 'long' })} {currentYear}
        </div>
        
        <button className="absolute right-1 h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100">
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      
      <div className="space-y-4">
        <div className="flex">
          {dayNames.map(day => (
            <div key={day} className="text-slate-500 w-9 font-normal text-xs text-center">
              {day}
            </div>
          ))}
        </div>
        
        {renderCalendar()}
      </div>
      
      {selectedDate && (
        <div className="mt-4 text-center text-sm">
          Selected: {selectedDate.toLocaleDateString()}
        </div>
      )}
    </div>
  );
}
Calendar.displayName = "Calendar"

export { Calendar }