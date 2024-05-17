import React, { useState } from 'react';
import Multiselect from 'multiselect-react-dropdown'
import './FilterContainer.css';

const FilterContainer = ({ onApplyFilters, contracts, header }) => {
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const handleApplyFilters = () => {
    // Call the parent component's function to apply filters
    onApplyFilters(selectedContracts, dateFrom, dateTo);
  };

  return (
    <div className="filter-container">
      <h2>{header}</h2>

      {/* Contract Multiselect */}
      <div className="multiselect-container">
        <Multiselect
          options={contracts.map((contract) => ({ key: contract.contract_name, value: contract.contract_name }))}
          selectedValues={selectedContracts.map((contract) => ({ key: contract, value: contract }))}
          onSelect={(selectedList) => setSelectedContracts(selectedList.map((item) => item.value))}
          onRemove={(selectedList) => setSelectedContracts(selectedList.map((item) => item.value))}
          displayValue="key"
          placeholder="Select contracts..."
          stype={{maxHeight: '200px', overflow: 'auto'}}
        />
      </div>

      {/* Date Range */}
      <label htmlFor="dateFrom">Date From:</label>
      <input type="date" id="dateFrom" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
      <label htmlFor="dateTo">Date To:</label>
      <input type="date" id="dateTo" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />

      {/* Apply Filters Button */}
      <button onClick={handleApplyFilters}>Apply Filters</button>
    </div>
  );
};

export default FilterContainer;
