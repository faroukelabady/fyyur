window.parseISOString = function parseISOString(s) {
  var b = s.split(/\D+/);
  return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
};


const deleteVenues = document.querySelectorAll('.delete-venue');
for (let deleteBtn of deleteVenues) {
  deleteBtn.onclick = function (e) {
    const venueId = e.target.dataset['id'];
    fetch('/venues/' + venueId, {
      method: 'DELETE',
    }).then(response => {
      if (response.redirected) {
        window.location.href = response.url;
      }
    }).catch(error => {
      console.log(error);
    })
  }
}


const deleteArtists = document.querySelectorAll('.delete-artist');
for (let deleteBtn of deleteArtists) {
  deleteBtn.onclick = function (e) {
    const artistId = e.target.dataset['id'];
    fetch('/artists/' + artistId, {
      method: 'DELETE',
    }).then(response => {
      if (response.redirected) {
        window.location.href = response.url;
      }
    }).catch(error => {
      console.log(error);
    })
  }
}