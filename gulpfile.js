var gulp = require('gulp');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var shell = require('gulp-shell');

gulp.task('sass', function() {
  return gulp.src('static/sass/*.scss')
    .pipe(sourcemaps.init())
    .pipe(sass({outputStyle: 'compressed'})).on('error', sass.logError)
    .pipe(sourcemaps.write('./'))
    .pipe(gulp.dest('static/css'))
});

gulp.task('flask', shell.task(['python invoice_app.py']));

gulp.task('watch', function() {
  gulp.watch('static/sass/*.scss', ['sass']);
});

gulp.task('default', ['sass', 'flask', 'watch']);
