import React, { useState, useEffect } from "react";
import Chart from "chart.js/auto";
import { Line } from "react-chartjs-2";
import './ValueChart.css';

const ValueChart = ({ transactions }) => {
    const [chartType, setChartType] = useState("Monthly");
    const [chartData, setChartData] = useState({ labels: [], datasets: [] });

    const generateLabels = (startDate, endDate, period) => {
        const labels = [];
        const currentDate = new Date(startDate);
        console.log(startDate, endDate, currentDate);

        while (currentDate <= endDate) {
            if (period === "Monthly") {
                labels.push(currentDate.toLocaleString("default", { month: "short", year: "numeric" }));
                currentDate.setMonth(currentDate.getMonth() + 1);
            } else if (period === "Daily") {
                labels.push(currentDate.toLocaleDateString());
                currentDate.setDate(currentDate.getDate() + 1);
            }
        }
    
        return labels;
    };

    const handleChange = (event) => {
        setChartType(event.target.value);
    };

    useEffect(() => {
        if (!transactions || transactions.length === 0) {
            return; // No transactions to render
        }

        const transactionDates = transactions.map(transaction => new Date(transaction.transact_dt));
        const startDate = new Date(Math.min(...transactionDates));
        const endDate = new Date(Math.max(...transactionDates));
        const labels = generateLabels(startDate, endDate, chartType);

        const transactionValueData = labels.map(label => {
            let sum = 0;
            if (chartType === "Monthly") {
                const [monthName, yearString] = label.split(" ");
                const year = parseInt(yearString, 10);
                const monthIndex = new Date(Date.parse(`1 ${monthName} 2000`)).getMonth();
    
                const monthStartDate = new Date(year, monthIndex, 1);
                const monthEndDate = new Date(year, monthIndex + 1, 0);
    
                transactions.forEach(transaction => {
                    const transactionDate = new Date(transaction.transact_dt);
                    if (transactionDate >= monthStartDate && transactionDate <= monthEndDate) {
                        sum += transaction.transact_amt;
                    }           
             });
            } else if (chartType === "Daily") {
                const labelDate = new Date(label);
                transactions.forEach(transaction => {
                    const transactionDate = new Date(transaction.transact_dt);
                    if (transactionDate.toDateString() === labelDate.toDateString()) {
                        sum += transaction.transact_amt;
                    }
                });
            }
            return sum;
        });

        const newChartData = {
            labels: labels,
            datasets: [
                {
                    label: "Transaction Value",
                    backgroundColor: "rgb(45,147,229)",
                    borderColor: "rgb(45,147,229)",
                    data: transactionValueData,
                }
            ],
        };

        setChartData(newChartData);
    }, [transactions, chartType]);

    return (
        <div className="chart-container">
            <label className="period-label" htmlFor="chartType">Period:</label>
            <select 
                className="period-dropdown"
                id="chartType" 
                value={chartType} 
                onChange={handleChange}
            >
                <option value="Monthly">Monthly</option>
                <option value="Daily">Daily</option>
            </select>
            <Line data={chartData} />
        </div>
    );
};

export default ValueChart;
