pipeline {
    agent {
        label 'slave-docker-7.7'
    }

    environment {
        HOME = """${sh(
                returnStdout: true,
                script: 'pwd -P'
        )}""".trim()
        PIPARGS='--user'
        PYPI_CREDENTIALS = credentials('PyPI')
        TESTPYPI_CREDENTIALS = credentials('TestPyPI')
    }

    stages {

        stage('Build and test in docker') {
            agent {
                dockerfile {
                    filename 'Dockerfile'
                    reuseNode true
                }
            }
            stages {
                stage('docker:Checkout') {
                    steps {
                        checkout scm
                    }
                }

                stage('docker:Test') {
                    steps {
                        sh 'make test'
                        junit testResults: 'tests/test-*.xml', allowEmptyResults: true
                    }
                }
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
                    tag "v*"
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
            deleteDir()
        }
    }
}
