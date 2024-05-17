import React from 'react';

const ArtifactsPage = ({ artifacts}) => {
  console.log('Artifacts:', artifacts);

  return (
    <div className="detail-page">
      <h1>Artifacts</h1>
      <ul>
        {artifacts.map((artifact, index) => (
          <li key={index}>
            <strong>{artifact.artifact_id}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ArtifactsPage;
