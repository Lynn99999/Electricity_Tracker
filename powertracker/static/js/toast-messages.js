document.querySelectorAll(".toast").forEach(function (toastElement) {
    const toast = new bootstrap.Toast(toastElement);

    toast.show();
});
