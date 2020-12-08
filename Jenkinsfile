pipeline {
    agent {
        dockerfile {
            filename 'Dockerfile'
        }
    }

    environment {
        HOME = """${sh(
                returnStdout: true,
                script: 'pwd -P'
        )}""".trim()
        PIPARGS = '--user'
        PYPI_CREDENTIALS = credentials('PyPI')
        TESTPYPI_CREDENTIALS = credentials('TestPyPI')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh 'make test'
                junit testResults: 'tests/test-*.xml', allowEmptyResults: true
            }
        }

        stage('Make distribution') {
            steps {
                sh 'make dist'
            }
        }

        stage('Push to TestPyPI') {
            when {
                anyOf {
                    tag "t*"
                }
            }

            steps {
                sh 'make publish-test'
            }
        }

        stage('Push official PyPI') {
            when {
                anyOf {
                    tag "v*"
                }
            }

            steps {
                sh 'make publish'
            }
        }
    }

    post {
        cleanup {
            sh 'make distclean'
            deleteDir()
        }
    }
}