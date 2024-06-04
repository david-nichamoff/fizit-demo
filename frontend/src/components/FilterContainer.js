import React, { useState } from 'react';
import Multiselect from 'multiselect-react-dropdown';
import './FilterContainer.css';

const FilterContainer = ({ onApplyFilters, items = [], dropdown_text, header, displayKey }) => {
  const [selectedItems, setSelectedItems] = useState([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const handleApplyFilters = () => {
    onApplyFilters(selectedItems, dateFrom, dateTo);
  };

  return (
    <div className="filter-container">
      <h2>{header}</h2>

      <div className="multiselect-container">
        <Multiselect
          options={items.map((item) => ({ key: item[displayKey], value: item[displayKey] }))}
          selectedValues={selectedItems.map((item) => ({ key: item, value: item }))}
          onSelect={(selectedList) => setSelectedItems(selectedList.map((item) => item.value))}
          onRemove={(selectedList) => setSelectedItems(selectedList.map((item) => item.value))}
          displayValue="key"
          placeholder={`Select ${dropdown_text.toLowerCase()}...`}
          style={{ maxHeight: '200px', overflow: 'auto' }}
        />
      </div>

      <div className="date-filter-container">
        <label htmlFor="dateFrom">Date From:</label>
        <input type="date" id="dateFrom" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <label htmlFor="dateTo">Date To:</label>
        <input type="date" id="dateTo" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        <div className="apply-filter-button-container">
          <button onClick={handleApplyFilters}>Apply Filter</button>
        </div>
      </div>
    </div>
  );
};

export default FilterContainer;