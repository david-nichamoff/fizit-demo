document.addEventListener("DOMContentLoaded", function () {
    const depositRadios = document.querySelectorAll("input[name='selected_deposit']");
    const settlementRadios = document.querySelectorAll("input[name='selected_settlement']");
    const depositDtInput = document.getElementById("selected-deposit-dt");
    const depositAmtInput = document.getElementById("selected-deposit-amt");
    const settlementIdxInput = document.getElementById("selected-settlement-idx");

    depositRadios.forEach((radio) => {
        radio.addEventListener("change", () => {
            try {
                depositDtInput.value = radio.getAttribute("data-deposit-dt");
                depositAmtInput.value = radio.getAttribute("data-deposit-amt");

                console.log("Selected deposit details:", {
                    deposit_dt: depositDtInput.value,
                    deposit_amt: depositAmtInput.value,
                });
            } catch (error) {
                console.error("Error selecting deposit:", error);
            }
        });
    });

    settlementRadios.forEach((radio) => {
        radio.addEventListener("change", () => {
            try {
                settlementIdxInput.value = radio.getAttribute("data-settlement-id");

                console.log("Selected settlement details:", {
                    settlement_idx: settlementIdxInput.value,
                });
            } catch (error) {
                console.error("Error selecting settlement:", error);
            }
        });
    });
});