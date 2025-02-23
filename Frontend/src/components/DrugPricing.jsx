import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DrugPricing.css';

const DrugPricing = () => {
    const [drugStats, setDrugStats] = useState(null);
    const [topDrugs, setTopDrugs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedDrug, setSelectedDrug] = useState('');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            // Get overall statistics
            const statsResponse = await axios.get('http://localhost:8001/api/drug-statistics');
            setDrugStats(statsResponse.data.data);

            // Get top drugs by spending
            const topDrugsResponse = await axios.get('http://localhost:8001/api/top-drugs');
            setTopDrugs(topDrugsResponse.data.data);
            
            setLoading(false);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoading(false);
        }
    };

    if (loading) return <div className="loading">Loading drug data...</div>;

    return (
        <div className="drug-pricing-container">
            <h2>Medicare Drug Price Analysis</h2>
            
            {/* Overall Statistics */}
            <div className="statistics-section">
                <h3>Overall Medicare Statistics (2022)</h3>
                {drugStats && (
                    <div className="stats-grid">
                        <div className="stat-card">
                            <h4>Utilization</h4>
                            <p>Total Claims: {drugStats.utilization.total_claims_2022.toLocaleString()}</p>
                            <p>Total Beneficiaries: {drugStats.utilization.total_beneficiaries_2022.toLocaleString()}</p>
                            <p>Total Dosage Units: {drugStats.utilization.total_dosage_units_2022.toLocaleString()}</p>
                        </div>
                        <div className="stat-card">
                            <h4>Spending Analysis</h4>
                            <p>Total Spending: ${drugStats.spending.total_spending_2022.toLocaleString()}</p>
                            <p>Average per Claim: ${drugStats.spending.avg_spending_per_claim_2022.toFixed(2)}</p>
                            <p>Average per Beneficiary: ${drugStats.spending.avg_spending_per_beneficiary_2022.toFixed(2)}</p>
                        </div>
                        <div className="stat-card">
                            <h4>Trends</h4>
                            <p>YoY Change (2021-2022): {(drugStats.trends.spending_change_2021_2022 * 100).toFixed(2)}%</p>
                            <p>5-Year CAGR: {(drugStats.trends.spending_cagr_2018_2022 * 100).toFixed(2)}%</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Top Drugs Table */}
            <div className="top-drugs-section">
                <h3>Top 10 Drugs by Total Spending</h3>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Drug Name</th>
                                <th>Total Spending (2022)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {topDrugs.map((drug, index) => (
                                <tr key={index}>
                                    <td>{index + 1}</td>
                                    <td>{drug.Brnd_Name}</td>
                                    <td>${drug.Tot_Spndng_2022.toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default DrugPricing; 