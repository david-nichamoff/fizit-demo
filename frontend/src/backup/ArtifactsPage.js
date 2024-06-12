import React, { useState, useEffect } from 'react';
import Pagination from './Pagination';
import { formatDateTime } from './Utils';
import FilterContainer from './FilterContainer';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import axios from 'axios';
import './ArtifactsPage.css';

const ArtifactsPage = ({ contracts, artifacts }) => {
  const itemsPerPage = 12;
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [filteredArtifacts, setFilteredArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  useEffect(() => {
    setIsInitialLoad(false);
  }, []);

  const applyFilters = (selectedContracts) => {
    setSelectedContracts(selectedContracts);
    setCurrentPage(1); 
    setFilteredArtifacts([]);
  };

  useEffect(() => {
    if (selectedContracts.length > 0) {
      const filteredArts = artifacts.filter(artifact => 
        selectedContracts.includes(artifact.contract_name)
      );
      setFilteredArtifacts(filteredArts);
    } else {
      setFilteredArtifacts(artifacts);
    }
  }, [selectedContracts, artifacts]);

  const totalPages = Math.ceil(filteredArtifacts.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, filteredArtifacts.length);
  const visibleArtifacts = filteredArtifacts.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleArtifactSelect = (artifact) => {
    setSelectedArtifact(artifact);
  };

  return (
    <div className="detail-page">
      <FilterContainer 
        onApplyFilters={applyFilters} 
        items={contracts} 
        dropdown_text="Contracts"
        header="Artifacts"
        displayKey="contract_name"
      />
      <div className="artifact-container">
        <div className="artifact-header">
          <div className="column-header string-column">Contract</div>
          <div className="column-header string-column">Artifact ID</div>
          <div className="column-header date-column">Added Date</div>
        </div>
        <ul className="artifact-list">
          {visibleArtifacts.map((artifact, index) => (
            <li 
              key={index} 
              className={`artifact-item ${artifact === selectedArtifact ? 'selected' : ''}`}
              onClick={() => handleArtifactSelect(artifact)}
            >
              <div className="artifact-column string-column">{artifact.contract_name}</div>
              <div className="artifact-column string-column">{artifact.artifact_id}</div>
              <div className="artifact-column date-column">{formatDateTime(artifact.added_dt)}</div>
            </li>
          ))}
        </ul>
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
      </div>
      {selectedArtifact && (
        <div className="artifact-viewer-container">
          <h2>Artifact Viewer</h2>
          <Worker workerUrl={`https://unpkg.com/pdfjs-dist@2.6.347/build/pdf.worker.min.js`}>
            <Viewer fileUrl={selectedArtifact.artifact_url} />
          </Worker>
        </div>
      )}
    </div>
  );
};

export default ArtifactsPage;