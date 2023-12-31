const { exec } = require("child_process");

//
// Handle the web API route used to request all sonar881 configurations.
// Pass the request to a python backend script, accepting the response
// through its stdout.
//
var getConfigurations = function(req, res) {
  console.log(`GET configuration names`);

  exec(`python configuration-enumerator.py`, (error, stdout, stderr) => {
    if (error) {
      console.log(`error: ${error.message}`);
      if (stderr) {
        console.log(`stderr: ${stderr}`);
      }
      res.status(error.code).send(error.message)
    } else {
      console.log(`Enumerated configuration names: ${stdout}`);
      res.set('Access-Control-Allow-Origin', '*');
      res.json(JSON.parse(stdout));
    }
  });
}

module.exports = getConfigurations;
