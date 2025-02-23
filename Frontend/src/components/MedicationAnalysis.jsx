import React, { useState, useEffect } from 'react';
import axios from 'axios';

const MedicationAnalysis = () => {
    const [selectedDrug, setSelectedDrug] = useState('');
    const [drugStats, setDrugStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('primary');

    const analyzeMedication = async (drugName) => {
        if (!drugName) return;
        
        setLoading(true);
        try {
            // Get drug statistics
            const response = await axios.get(`http://localhost:8001/api/drug-statistics/${drugName}`);
            setDrugStats(response.data.data);
        } catch (error) {
            console.error('Error fetching drug data:', error);
        }
        setLoading(false);
    };

    // Update analysis when medication changes
    useEffect(() => {
        if (selectedDrug) {
            analyzeMedication(selectedDrug);
        }
    }, [selectedDrug]);

    const renderMedicareCoverage = () => {
        if (!drugStats) return null;

        const years = ['2018', '2019', '2020', '2021', '2022'];
        
        return (
            <div className="pricing-section">
                <h3>Medicare Coverage Analysis</h3>
                <div className="stats-grid">
                    <div className="stat-card">
                        <h4>Utilization Metrics</h4>
                        {years.map(year => (
                            <div key={year} className="year-stats">
                                <h5>{year}</h5>
                                <p>Claims: {drugStats.utilization[`Tot_Clms_${year}`]?.toLocaleString() || 'N/A'}</p>
                                <p>Beneficiaries: {drugStats.utilization[`Tot_Benes_${year}`]?.toLocaleString() || 'N/A'}</p>
                                <p>Dosage Units: {drugStats.utilization[`Tot_Dsg_Unts_${year}`]?.toLocaleString() || 'N/A'}</p>
                            </div>
                        ))}
                    </div>
                    <div className="stat-card">
                        <h4>Cost Analysis</h4>
                        {years.map(year => (
                            <div key={year} className="year-stats">
                                <h5>{year}</h5>
                                <p>Total Spending: ${drugStats.spending[`Tot_Spndng_${year}`]?.toLocaleString() || 'N/A'}</p>
                                <p>Avg per Claim: ${drugStats.spending[`Avg_Spnd_Per_Clm_${year}`]?.toFixed(2) || 'N/A'}</p>
                                <p>Avg per Beneficiary: ${drugStats.spending[`Avg_Spnd_Per_Bene_${year}`]?.toFixed(2) || 'N/A'}</p>
                            </div>
                        ))}
                    </div>
                    <div className="stat-card">
                        <h4>Trend Analysis</h4>
                        <p>YoY Change (2021-2022): {drugStats.trends.spending_change_2021_2022 ? 
                            `${(drugStats.trends.spending_change_2021_2022 * 100).toFixed(2)}%` : 'N/A'}</p>
                        <p>5-Year CAGR: {drugStats.trends.spending_cagr_2018_2022 ? 
                            `${(drugStats.trends.spending_cagr_2018_2022 * 100).toFixed(2)}%` : 'N/A'}</p>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="medication-analysis">
            {/* Your existing medication search UI */}
            
            {/* Analysis Tabs */}
            <div className="analysis-tabs">
                <button 
                    className={`tab-btn ${activeTab === 'primary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('primary')}>
                    💊 Primary Details
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'similar' ? 'active' : ''}`}
                    onClick={() => setActiveTab('similar')}>
                    🔄 Similar Medications
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'sideEffects' ? 'active' : ''}`}
                    onClick={() => setActiveTab('sideEffects')}>
                    ⚠️ Side Effects
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'medicare' ? 'active' : ''}`}
                    onClick={() => setActiveTab('medicare')}>
                    💰 Medicare Coverage
                </button>
            </div>

            {/* Content based on active tab */}
            {activeTab === 'medicare' && renderMedicareCoverage()}
            
            {loading && <div className="loading">Loading analysis...</div>}
        </div>
    );
};

export default MedicationAnalysis; 