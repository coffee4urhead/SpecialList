let map;
let userMarker;
let followerMarkers = [];

function initMap() {
    map = L.map('map').setView([0, 0], 2);

    setTimeout(() => {
        const mapElement = document.getElementById('map');
        mapElement.style.height = '20rem';
        mapElement.style.width = '100%';
        mapElement.style.borderRadius = '12px';
        mapElement.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';

        map.invalidateSize();
    }, 100);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const userPos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };

                map.setView([userPos.lat, userPos.lng], 12);

                const userIcon = L.icon({
                    iconUrl: "../../static/images/user-marker.png",
                    iconSize: [40, 40],
                    iconAnchor: [20, 40],
                    popupAnchor: [0, -40]
                });

                userMarker = L.marker([userPos.lat, userPos.lng], {
                    icon: userIcon,
                    title: "Your Location"
                }).addTo(map)
                .bindPopup("Your Location");

                sendLocationToServer(userPos.lat, userPos.lng);
            },
            error => {
                console.error("Error getting location:", error);
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}
document.addEventListener('DOMContentLoaded', initMap);

setInterval(() => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const userPos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                sendLocationToServer(userPos.lat, userPos.lng);

                if (userMarker) {
                    userMarker.setLatLng([userPos.lat, userPos.lng]);
                }
            },
            error => console.error("Error updating location:", error)
        );
    }
}, 300000);