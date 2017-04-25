module.exports = function (grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('bower.json'),
        bower_concat: {
            all: {
                dest: 'darecms/static/combined.js',
                cssDest: 'darecms/static/combined.css',
                callback: function (mainFiles, component) {
                    if (component === 'select2') {
                        // the default select2 file doesn't contain full functionality and we want the full thing
                        return mainFiles.map(function(filepath) {
                            return filepath.replace('select2.js', 'select2.full.js');
                        });
                    } else if (component === 'materialize') {
                        return mainFiles.concat([
                            process.cwd() + '/bower_components/materialize/dist/css/materialize.min.css',
                            process.cwd() + '/bower_components/materialize/dist/js/materialize.min.js'
                        ]);
                    } else if (component === 'jquery-ui') {
                        return mainFiles.concat([process.cwd() + '/bower_components/jquery-ui/themes/ui-lightness/jquery-ui.css']);
                    } else if (component === 'jquery') {
                        // jquery-datetextentry doesn't have a bower.json so we're manually added it to the files we concat
                        // TODO: make a pull request to the jquery-datetextentry to give them bower support
                        return mainFiles.concat([
                            process.cwd() + '/uber/static/deps/jquery-datetextentry/jquery.datetextentry.js',
                            process.cwd() + '/uber/static/deps/jquery-datetextentry/jquery.datetextentry.css'
                        ]);
                    } else if (component === 'datatables') {
                        mainFiles = mainFiles.map(function(filepath) {
                            return filepath.replace('jquery.dataTables.css', 'dataTables.bootstrap.css')
                        });
                        mainFiles = mainFiles.concat([process.cwd() + '/bower_components/datatables/media/js/dataTables.bootstrap.js']);
                        return mainFiles;
                    } else {
                        return mainFiles;
                    }
                }
            }
        }
    });
    grunt.loadNpmTasks('grunt-bower-concat');
    grunt.registerTask('default', ['bower_concat']);
};
